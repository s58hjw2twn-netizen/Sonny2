"""Protected MCP ASGI integration checks using an in-process HTTP transport."""
import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from sonny.mcp_protected_local import build_app, mcp
from sonny.mcp_resource_auth import ResourceAuthConfig


def test_protected_mcp_http_access():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    config = ResourceAuthConfig("https://issuer.example", "https://sonny.example/mcp", pub)
    now = datetime.now(timezone.utc)
    claims = dict(iss=config.issuer, aud=config.audience, sub="pilot",
                  iat=now, exp=now + timedelta(minutes=5), scope=config.required_scope)
    good = jwt.encode(claims, private, algorithm="RS256")
    bad = jwt.encode({**claims, "scope": "other"}, private, algorithm="RS256")

    # Building the Streamable HTTP ASGI app initializes the SDK session manager.
    # This must happen before entering its lifespan context.
    protected_app = build_app(config)

    async def run():
        async with mcp.session_manager.run():
            transport = httpx.ASGITransport(app=protected_app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                for headers in ({}, {"Authorization": "Bearer invalid"},
                                {"Authorization": "Bearer " + bad}):
                    response = await client.post(
                        "/mcp", headers=headers,
                        json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {"protocolVersion": "2025-03-26",
                                         "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
                    )
                    assert response.status_code == 401
                response = await client.post(
                    "/mcp",
                    headers={"Authorization": "Bearer " + good,
                             "Accept": "application/json, text/event-stream",
                             "Content-Type": "application/json"},
                    json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2025-03-26",
                                     "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
                )
                assert response.status_code == 200, response.text
                assert "result" in response.text

    asyncio.run(run())
