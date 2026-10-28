"""ASGI boundary tests: no requests reach the protected app without a valid token."""
import asyncio
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from sonny.mcp_auth_boundary import BearerAuthBoundary
from sonny.mcp_resource_auth import ResourceAuthConfig


def test_boundary_denies_unauthorized_and_allows_valid_token():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    config = ResourceAuthConfig("https://issuer.example", "https://sonny.example/mcp", pub)
    now = datetime.now(timezone.utc)
    claims = dict(iss=config.issuer, aud=config.audience, sub="pilot",
                  iat=now, exp=now + timedelta(minutes=5), scope=config.required_scope)
    good = jwt.encode(claims, key, algorithm="RS256")
    expired = jwt.encode({**claims, "exp": now - timedelta(minutes=1)}, key, algorithm="RS256")
    calls = []

    async def protected(scope, receive, send):
        calls.append(scope["path"])
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    app = BearerAuthBoundary(protected, config)

    async def request(auth_headers, path="/mcp"):
        events = []
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        async def send(event):
            events.append(event)
        await app({"type": "http", "path": path, "headers": auth_headers}, receive, send)
        return events[0]["status"]

    async def checks():
        assert await request([]) == 401
        assert await request([(b"authorization", b"Bearer nonsense")]) == 401
        assert await request([(b"authorization", ("Bearer " + expired).encode())]) == 401
        assert await request([(b"authorization", ("Bearer " + good).encode())] * 2) == 401
        assert await request([(b"authorization", ("Bearer " + good).encode())], "/other") == 200
        assert calls == ["/other"]

    asyncio.run(checks())
