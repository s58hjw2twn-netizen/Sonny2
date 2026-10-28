"""Authenticated local-pilot regression tests. All keys/accounts are public fixtures."""
import time
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from sonny_one.pilot_app import COOKIE, ISSUER, create_app
from sonny_one.pilot_store import PilotStore, password_hash, verify_password

ORIGIN = 'http://127.0.0.1:8766'
KEY = 'public-test-fixture-signing-key-not-for-real-use'
PASSWORD = 'public-test-password-only'


def local_client(app):
    async def loopback(scope, receive, send):
        if scope['type'] == 'http':
            scope = {**scope, 'client': ('127.0.0.1', 12345)}
        await app(scope, receive, send)
    return TestClient(loopback, base_url=ORIGIN, headers={'Origin': ORIGIN})


@pytest.fixture
def pilot(tmp_path):
    path = tmp_path / 'pilot.db'
    store = PilotStore(path)
    alice = store.create_user('alice-demo', PASSWORD)
    bob = store.create_user('bob-demo', PASSWORD)
    app = create_app(db_path=path, signing_key=KEY, origin=ORIGIN)
    with local_client(app) as a, local_client(app) as b:
        assert a.post('/auth/login', json={'username': 'alice-demo', 'password': PASSWORD}).status_code == 200
        assert b.post('/auth/login', json={'username': 'bob-demo', 'password': PASSWORD}).status_code == 200
        yield app, store, a, b, alice, bob


def send(client, message='What do you remember?', request_id=None, **extra):
    return client.post('/api/chat', json={'message': message, 'request_id': request_id or str(uuid.uuid4()), **extra})


def test_startup_requires_secret_and_loopback_origin(tmp_path, monkeypatch):
    monkeypatch.delenv('SONNY_ONE_AUTH_SECRET', raising=False)
    with pytest.raises(RuntimeError):
        create_app(db_path=tmp_path/'missing.db')
    for origin in ['https://example.com', ORIGIN+'/', ORIGIN+'?x=1', 'http://user@localhost:8766']:
        with pytest.raises(RuntimeError):
            create_app(db_path=tmp_path/'invalid.db', signing_key=KEY, origin=origin)


def test_passwords_salted_and_never_stored_plaintext(tmp_path):
    store = PilotStore(tmp_path/'p.db')
    store.create_user('alice-demo', PASSWORD)
    encoded = store.account('alice-demo')['password_hash']
    assert PASSWORD not in encoded
    assert verify_password(PASSWORD, encoded)
    assert not verify_password('wrong', encoded)
    assert encoded != password_hash(PASSWORD)
    with pytest.raises(ValueError):
        store.create_user('invalid name', PASSWORD)


def test_unauthenticated_and_spoofed_identity_rejected(pilot):
    app, _, _, _, owner, _ = pilot
    with local_client(app) as client:
        paths = [('GET', '/api/workspace', None), ('PATCH', '/api/workspace', {'goal':'steal'}),
                 ('DELETE', '/api/workspace', None), ('DELETE', '/api/conversation', None),
                 ('POST', '/api/chat', {'message':'hi','request_id':str(uuid.uuid4())}),
                 ('POST', '/api/memories', {'statement':'fake','consent':True}),
                 ('POST', '/auth/logout', None)]
        for method, path, body in paths:
            assert client.request(method, path, json=body, headers={'X-User-ID':owner}).status_code == 401


def test_cookie_flags_and_generic_login_failure(pilot):
    app, _, _, _, _, _ = pilot
    with local_client(app) as client:
        wrong = client.post('/auth/login', json={'username':'alice-demo','password':'wrong'})
        missing = client.post('/auth/login', json={'username':'nobody','password':'wrong'})
        assert wrong.status_code == missing.status_code == 401
        assert wrong.json() == missing.json()
        response = client.post('/auth/login', json={'username':'alice-demo','password':PASSWORD})
        cookie = response.headers['set-cookie'].lower()
        assert 'httponly' in cookie and 'samesite=strict' in cookie and 'max-age=3600' in cookie
        assert 'domain=' not in cookie


def test_expired_forged_missing_claim_and_revoked_sessions_rejected(pilot):
    app, store, a, _, owner, _ = pilot
    token = a.cookies.get(COOKIE)
    payload = jwt.decode(token, KEY, algorithms=['HS256'], issuer=ISSUER)
    variants = [jwt.encode(payload, 'different-public-test-key', algorithm='HS256'),
                jwt.encode({**payload,'exp':int(time.time())-1},KEY,algorithm='HS256'),
                jwt.encode({k:v for k,v in payload.items() if k!='exp'},KEY,algorithm='HS256')]
    for altered in variants:
        with local_client(app) as client:
            client.cookies.set(COOKIE, altered)
            assert client.get('/api/workspace').status_code == 401
    assert a.post('/auth/logout').status_code == 200
    assert not store.session_valid(owner, payload['sid'])
    with local_client(app) as client:
        client.cookies.set(COOKIE, token)
        assert client.get('/api/workspace').status_code == 401


def test_cross_origin_host_and_remote_requests_rejected(pilot):
    app, _, a, _, _, _ = pilot
    for origin in ['https://attacker.invalid', 'null', 'http://localhost:8766']:
        assert a.patch('/api/workspace',json={'goal':'bad'},headers={'Origin':origin}).status_code == 403
    assert a.get('/api/workspace',headers={'Host':'attacker.invalid'}).status_code == 400
    with TestClient(app, base_url=ORIGIN) as remote:
        assert remote.get('/').status_code == 403
    with local_client(app) as client:
        client.headers.pop('Origin')
        assert client.post('/auth/login',json={'username':'alice-demo','password':PASSWORD}).status_code == 403


def test_memory_consent_provenance_correction_and_forgetting(pilot):
    _, store, a, _, owner, _ = pilot
    assert a.post('/api/memories',json={'statement':'Sample fact','consent':False}).status_code == 400
    assert a.post('/api/memories',json={'statement':'Sample fact','consent':'yes'}).status_code == 422
    data = a.post('/api/memories',json={'statement':'Sample fact','consent':True}).json()
    fact = data['memories'][0]
    assert fact['source'] == 'explicit_user_statement' and fact['approved_at']
    assert 'Sample fact' in send(a).json()['text']
    corrected = a.patch('/api/memories/'+fact['id'],json={'statement':'Corrected sample','consent':True,'revision':1})
    assert corrected.status_code == 200 and corrected.json()['memories'][0]['revision'] == 2
    stale = a.patch('/api/memories/'+fact['id'],json={'statement':'Stale','consent':True,'revision':1})
    assert stale.status_code == 409
    assert 'Sample fact' not in send(a).json()['text']
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM fact_events WHERE owner=? AND event='CORRECTED'",(owner,)).fetchone()[0] == 1
    assert a.delete('/api/memories/'+fact['id']).status_code == 200
    assert 'Corrected sample' not in send(a).json()['text']


def test_cross_account_objects_and_context_cannot_be_spoofed(pilot):
    _, _, a, b, owner, _ = pilot
    a.patch('/api/workspace',json={'goal':'ALICE PRIVATE GOAL'})
    fact = a.post('/api/memories',json={'statement':'ALICE PRIVATE FACT','consent':True}).json()['memories'][0]
    assert b.patch('/api/memories/'+fact['id'],json={'statement':'steal','consent':True,'revision':1}).status_code == 404
    assert b.delete('/api/memories/'+fact['id']).status_code == 404
    assert 'ALICE PRIVATE' not in str(b.get('/api/workspace',headers={'X-User-ID':owner}).json())
    assert 'ALICE PRIVATE' not in send(b).json()['text']
    assert send(b, memories=['injected']).status_code == 422
    assert send(b, user_id=owner).status_code == 422
    assert b.patch('/api/workspace',json={'goal':'Bob','owner':owner}).status_code == 422
    b.delete('/api/workspace')
    assert a.get('/api/workspace').json()['memories'][0]['statement'] == 'ALICE PRIVATE FACT'


def test_restart_idempotency_and_erasure(pilot):
    app, store, a, b, owner, _ = pilot
    a.patch('/api/workspace',json={'goal':'Persist sample goal'})
    a.post('/api/memories',json={'statement':'Persist sample fact','consent':True})
    request_id = str(uuid.uuid4())
    first = send(a, request_id=request_id)
    assert first.json() == send(a, request_id=request_id).json()
    assert len(a.get('/api/workspace').json()['messages']) == 2
    assert send(a,'different',request_id=request_id).status_code == 409
    restarted = create_app(db_path=store.path, signing_key=KEY, origin=ORIGIN)
    with local_client(restarted) as fresh:
        fresh.cookies.set(COOKIE,a.cookies.get(COOKIE))
        restored = fresh.get('/api/workspace').json()
        assert restored['goal'] == 'Persist sample goal' and len(restored['messages']) == 2
        assert restored['memories'][0]['statement'] == 'Persist sample fact'
        erased = fresh.delete('/api/workspace').json()
        assert erased['memories'] == erased['messages'] == []
        assert 'Persist sample fact' not in send(fresh,request_id=request_id).json()['text']
    with store.connect() as db:
        assert db.execute('SELECT count(*) FROM fact_events WHERE owner=?',(owner,)).fetchone()[0] == 0


def test_failed_chat_transaction_leaves_no_partial_turn(pilot):
    _, store, a, _, owner, _ = pilot
    def broken(*args):
        raise RuntimeError('simulated responder failure')
    with pytest.raises(RuntimeError):
        store.reply(owner,'hello',str(uuid.uuid4()),broken)
    assert a.get('/api/workspace').json()['messages'] == []


def test_login_rate_limit(tmp_path):
    app = create_app(db_path=tmp_path/'rate.db',signing_key=KEY,origin=ORIGIN,login_limit=2)
    with local_client(app) as client:
        for _ in range(2):
            assert client.post('/auth/login',json={'username':'nobody','password':'wrong'}).status_code == 401
        response = client.post('/auth/login',json={'username':'nobody','password':'wrong'})
        assert response.status_code == 429 and response.headers['retry-after'] == '60'


def test_parallel_retries_produce_one_turn(pilot):
    from concurrent.futures import ThreadPoolExecutor
    _, store, _, _, owner, _ = pilot
    request_id = str(uuid.uuid4())
    responder = lambda *args: {'text':'One response','mode':'deterministic-demo','memory_count':0}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.reply(owner,'hello',request_id,responder), range(4)))
    assert results == [results[0]] * 4
    assert len(store.workspace(owner)['messages']) == 2


def test_local_signing_config_is_private_stable_and_not_overwritten(tmp_path):
    from scripts.start_sonny_one_pilot import load_or_create_config
    import os
    config = load_or_create_config(tmp_path)
    assert len(config['signing_key']) >= 32
    assert load_or_create_config(tmp_path) == config
    if os.name == 'posix':
        assert (tmp_path/'config.json').stat().st_mode & 0o077 == 0
    (tmp_path/'config.json').write_text('{invalid')
    with pytest.raises(ValueError, match='not overwritten'):
        load_or_create_config(tmp_path)
    assert (tmp_path/'config.json').read_text() == '{invalid'


def test_fact_limit_and_history_bound(pilot):
    _, store, _, _, owner, _ = pilot
    for index in range(50):
        store.save_fact(owner, f'Sample fact {index}')
    with pytest.raises(ValueError, match='full'):
        store.save_fact(owner,'extra fact')
    for index in range(55):
        store.reply(owner,str(index),str(uuid.uuid4()),lambda *args:{'text':'sample'})
    history = store.workspace(owner)['messages']
    assert len(history) == 100 and history[0]['text'] == '5'
