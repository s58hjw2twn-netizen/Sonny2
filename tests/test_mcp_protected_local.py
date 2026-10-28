"""Protected MCP ASGI integration checks using an in-process HTTP transport."""
import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from sonny.mcp_protected_local import build_app, create_mcp_server
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
    server = create_mcp_server()
    protected_app = build_app(config, server=server)

    async def run():
        async with server.session_manager.run():
            transport = httpx.ASGITransport(app=protected_app)
            async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8766") as client:
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

                # Verify the authorized tool surface, not merely initialization.
                authorized_headers = {
                    "Authorization": "Bearer " + good,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2025-03-26",
                }
                listed = await client.post(
                    "/mcp", headers=authorized_headers,
                    json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                )
                assert listed.status_code == 200, listed.text
                assert '"protocol_status"' in listed.text
                assert '"tools"' in listed.text

                called = await client.post(
                    "/mcp", headers=authorized_headers,
                    json={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "protocol_status", "arguments": {}}},
                )
                assert called.status_code == 200, called.text
                assert '"Sonny ONE"' in called.text
                assert '"protected-local"' in called.text

                # A valid signature with insufficient scope must not list or call tools.
                for method, params in (
                    ("tools/list", {}),
                    ("tools/call", {"name": "protocol_status", "arguments": {}}),
                ):
                    denied = await client.post(
                        "/mcp",
                        headers={**authorized_headers, "Authorization": "Bearer " + bad},
                        json={"jsonrpc": "2.0", "id": 4, "method": method, "params": params},
                    )
                    assert denied.status_code == 401

    asyncio.run(run())


def test_opt_in_discovery_preserves_mcp_authorization():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    config = ResourceAuthConfig("https://issuer.example", "https://sonny.example/mcp", pub)
    server = create_mcp_server()
    app = build_app(config, resource_url=config.audience, server=server)

    async def run():
        async with server.session_manager.run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8766",
            ) as client:
                discovery = await client.get("/.well-known/oauth-protected-resource/mcp")
                assert discovery.status_code == 200
                assert discovery.json()["resource"] == config.audience
                assert discovery.json()["authorization_servers"] == [config.issuer]
                denied = await client.post(
                    "/mcp",
                    headers={"Accept": "application/json, text/event-stream"},
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                )
                assert denied.status_code == 401
                assert 'resource_metadata="https://sonny.example/.well-known/oauth-protected-resource/mcp"' in denied.headers["www-authenticate"]
                assert (await client.get("/")).status_code == 401

    asyncio.run(run())


def test_discovery_rejects_mismatched_resource_audience():
    import pytest
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    config = ResourceAuthConfig("https://issuer.example", "https://sonny.example/mcp", pub)
    with pytest.raises(ValueError, match="audience"):
        build_app(config, resource_url="https://other.example/mcp")


def test_protected_app_uses_explicit_verifier_for_read_only_tool():
    config = ResourceAuthConfig(
        "https://issuer.example", "https://sonny.example/mcp", "unused-pinned-key"
    )
    server = create_mcp_server()
    seen = []

    def verifier(token, supplied_config):
        seen.append(token)
        if token != "approved-test-token":
            raise ValueError("rejected")

    app = build_app(config, server=server, token_verifier=verifier)

    async def run():
        async with server.session_manager.run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8766",
            ) as client:
                headers = {
                    "Authorization": "Bearer approved-test-token",
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                }
                response = await client.post(
                    "/mcp", headers=headers,
                    json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2025-03-26",
                                     "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
                )
                assert response.status_code == 200, response.text
                denied = await client.post(
                    "/mcp", headers={**headers, "Authorization": "Bearer rejected-token"},
                    json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                )
                assert denied.status_code == 401
                assert seen == ["approved-test-token", "rejected-token"]

    asyncio.run(run())


def test_environment_selects_jwks_verifier_only_when_explicit(monkeypatch):
    from sonny.mcp_protected_local import config_from_environment
    monkeypatch.setenv("SONNY_MCP_AUTH_MODE", "jwks")
    monkeypatch.setenv("SONNY_MCP_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONNY_MCP_OAUTH_AUDIENCE", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_JWKS_URI", "https://issuer.example/keys")
    monkeypatch.delenv("SONNY_MCP_OAUTH_PUBLIC_KEY_PEM", raising=False)
    config, verifier = config_from_environment()
    assert config.jwks_uri == "https://issuer.example/keys"
    assert verifier.__name__ == "verify_jwks_resource_token"


def test_environment_defaults_to_pinned_key_verifier(monkeypatch):
    from sonny.mcp_protected_local import config_from_environment
    monkeypatch.delenv("SONNY_MCP_AUTH_MODE", raising=False)
    monkeypatch.setenv("SONNY_MCP_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONNY_MCP_OAUTH_AUDIENCE", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_PUBLIC_KEY_PEM", "configured-test-key")
    monkeypatch.delenv("SONNY_MCP_OAUTH_JWKS_URI", raising=False)
    config, verifier = config_from_environment()
    assert config.public_key_pem == "configured-test-key"
    assert verifier is None


def test_environment_rejects_unknown_auth_mode(monkeypatch):
    import pytest
    from sonny.mcp_protected_local import config_from_environment
    monkeypatch.setenv("SONNY_MCP_AUTH_MODE", "automatic")
    with pytest.raises(ValueError, match="SONNY_MCP_AUTH_MODE"):
        config_from_environment()
