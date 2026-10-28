"""Authenticated, loopback-only pilot. No external APIs or research integration."""
from collections import defaultdict, deque
import os
import ipaddress
import secrets
import threading
import time
from urllib.parse import urlsplit
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from sonny_one.pilot_store import PilotStore, password_hash, verify_password
from sonny_one.web_app import WEB, ChatRequest, chat as demo_reply

COOKIE = 'sonny_one_session'
ISSUER = 'sonny-one-local-pilot'
TTL = 3600


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Login(Input):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class Goal(Input):
    goal: str = Field(min_length=1, max_length=500)

    @field_validator('goal')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Goal must not be blank')
        return value.strip()


class Fact(Input):
    statement: str = Field(min_length=1, max_length=500)
    consent: StrictBool

    @field_validator('statement')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Fact must not be blank')
        return value.strip()


class Correction(Fact):
    revision: int = Field(ge=1)


class Message(Input):
    message: str = Field(min_length=1, max_length=4000)
    request_id: UUID

    @field_validator('message')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Message must not be blank')
        return value.strip()


def create_app(*, db_path=None, signing_key=None, origin=None, login_limit=10):
    key = signing_key or os.getenv('SONNY_ONE_AUTH_SECRET', '')
    if len(key) < 32:
        raise RuntimeError('Set SONNY_ONE_AUTH_SECRET to a private random value of at least 32 characters')
    origin = origin or os.getenv('SONNY_ONE_ORIGIN', 'http://127.0.0.1:8766')
    parsed = urlsplit(origin)
    if (parsed.hostname not in {'127.0.0.1', 'localhost', '::1'} or parsed.scheme not in {'http', 'https'}
            or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise RuntimeError('Local pilot origin must be an exact loopback HTTP(S) origin without a path')
    store = PilotStore(db_path or os.getenv('SONNY_ONE_DB', 'sonny_one_pilot.db'))
    secure = parsed.scheme == 'https'
    app = FastAPI(title='Sonny ONE local authenticated pilot', docs_url=None, redoc_url=None)
    app.state.store = store
    app.mount('/assets', StaticFiles(directory=WEB), name='assets')
    attempts = defaultdict(deque)
    limiter_lock = threading.Lock()
    dummy_hash = password_hash('public-dummy-password-for-timing', '00' * 16)

    @app.middleware('http')
    async def local_boundary(request, call_next):
        try:
            local = request.client is not None and ipaddress.ip_address(request.client.host).is_loopback
        except ValueError:
            local = False
        if not local:
            response = JSONResponse({'detail': 'Loopback access only'}, status_code=403)
        elif request.headers.get('host') != parsed.netloc:
            response = JSONResponse({'detail': 'Invalid local host'}, status_code=400)
        elif request.method not in {'GET', 'HEAD', 'OPTIONS'} and request.headers.get('origin') != origin:
            response = JSONResponse({'detail': 'Same-origin browser request required'}, status_code=403)
        else:
            response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        return response

    def authenticated(request: Request):
        token = request.cookies.get(COOKIE, '')
        try:
            payload = jwt.decode(token, key, algorithms=['HS256'], issuer=ISSUER,
                                 options={'require': ['sub', 'sid', 'iss', 'iat', 'exp']})
            owner, sid = payload['sub'], payload['sid']
            if not isinstance(owner, str) or not isinstance(sid, str) or not store.session_valid(owner, sid):
                raise ValueError('Revoked session')
            return owner, sid
        except (jwt.PyJWTError, ValueError, TypeError):
            raise HTTPException(401, 'Sign in required')

    @app.get('/')
    def home():
        return FileResponse(WEB / 'pilot.html')

    @app.get('/api/status')
    def status():
        return {'mode': 'local-authenticated-demo', 'model_connected': False, 'api_cost': 0,
                'server_persistence': True}

    @app.post('/auth/login')
    def login(body: Login, request: Request, response: Response):
        address = request.client.host if request.client else 'local'
        now = time.monotonic()
        with limiter_lock:
            if len(attempts) >= 1024 and address not in attempts:
                attempts.pop(next(iter(attempts)))
            bucket = attempts[address]
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= login_limit:
                raise HTTPException(429, 'Too many sign-in attempts; wait a minute', headers={'Retry-After': '60'})
            bucket.append(now)
        account = store.account(body.username)
        valid = verify_password(body.password, account['password_hash'] if account else dummy_hash)
        if not account or not valid:
            raise HTTPException(401, 'Invalid username or password')
        # Starting a new login revokes the previous valid session in this browser.
        try:
            _, old_sid = authenticated(request)
            store.revoke_session(old_sid)
        except HTTPException:
            pass
        owner, sid = account['id'], secrets.token_urlsafe(32)
        expires = int(time.time()) + TTL
        store.add_session(owner, sid, expires)
        token = jwt.encode({'sub': owner, 'sid': sid, 'iss': ISSUER,
                            'iat': int(time.time()), 'exp': expires}, key, algorithm='HS256')
        response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, secure=secure,
                            samesite='strict', path='/')
        return {'signed_in': True, 'username': account['username']}

    @app.post('/auth/logout')
    def logout(response: Response, session=Depends(authenticated)):
        store.revoke_session(session[1])
        response.delete_cookie(COOKIE, path='/', httponly=True, secure=secure, samesite='strict')
        return {'signed_out': True}

    @app.get('/api/workspace')
    def workspace(session=Depends(authenticated)):
        return store.workspace(session[0])

    @app.patch('/api/workspace')
    def goal(body: Goal, session=Depends(authenticated)):
        store.set_goal(session[0], body.goal)
        return store.workspace(session[0])

    @app.delete('/api/workspace')
    def erase(session=Depends(authenticated)):
        store.erase(session[0])
        return store.workspace(session[0])

    @app.delete('/api/conversation')
    def clear(session=Depends(authenticated)):
        store.clear_chat(session[0])
        return store.workspace(session[0])

    @app.post('/api/memories')
    def remember(body: Fact, session=Depends(authenticated)):
        if body.consent is not True:
            raise HTTPException(400, 'Explicit memory consent required')
        try:
            store.save_fact(session[0], body.statement)
        except ValueError as exc:
            raise HTTPException(409, str(exc))
        return store.workspace(session[0])

    @app.patch('/api/memories/{fact_id}')
    def correct(fact_id: str, body: Correction, session=Depends(authenticated)):
        if body.consent is not True:
            raise HTTPException(400, 'Explicit memory consent required')
        outcome = store.correct_fact(session[0], fact_id, body.statement, body.revision)
        if outcome == 'missing':
            raise HTTPException(404, 'Fact not found')
        if outcome == 'conflict':
            raise HTTPException(409, 'Fact changed; reload before correcting it')
        return store.workspace(session[0])

    @app.delete('/api/memories/{fact_id}')
    def forget(fact_id: str, session=Depends(authenticated)):
        if not store.forget_fact(session[0], fact_id):
            raise HTTPException(404, 'Fact not found')
        return store.workspace(session[0])

    @app.post('/api/chat')
    def chat(body: Message, session=Depends(authenticated)):
        def responder(message, goal, memories):
            return demo_reply(ChatRequest(message=message, goal=goal, memories=memories))
        try:
            return store.reply(session[0], body.message, str(body.request_id), responder)
        except ValueError as exc:
            raise HTTPException(409, str(exc))

    return app
