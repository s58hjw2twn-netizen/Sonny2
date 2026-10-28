"""The staging listener must fail closed before any network bind."""
import pytest
from sonny.mcp_staging_entrypoint import create_staging_app


def test_staging_requires_explicit_approval(monkeypatch):
    monkeypatch.delenv("SONNY_MCP_STAGING_APPROVED", raising=False)
    with pytest.raises(RuntimeError, match="explicit approval"):
        create_staging_app()


def test_staging_requires_resource_url(monkeypatch):
    monkeypatch.setenv("SONNY_MCP_STAGING_APPROVED", "true")
    monkeypatch.delenv("SONNY_MCP_PUBLIC_RESOURCE_URL", raising=False)
    with pytest.raises(KeyError, match="SONNY_MCP_PUBLIC_RESOURCE_URL"):
        create_staging_app()


def test_staging_builds_protected_app_with_valid_configuration(monkeypatch):
    import asyncio
    import httpx
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    monkeypatch.setenv("SONNY_MCP_STAGING_APPROVED", "true")
    monkeypatch.setenv("SONNY_MCP_PUBLIC_RESOURCE_URL", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONNY_MCP_OAUTH_AUDIENCE", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_PUBLIC_KEY_PEM", public)
    app = create_staging_app()

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
        ) as client:
            metadata = await client.get("/.well-known/oauth-protected-resource/mcp")
            assert metadata.status_code == 200
            assert metadata.json()["resource"] == "https://sonny.example/mcp"
            denied = await client.get("/mcp")
            assert denied.status_code == 401
            assert "resource_metadata=" in denied.headers["www-authenticate"]

    asyncio.run(run())


def test_staging_rejects_mismatched_audience(monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    monkeypatch.setenv("SONNY_MCP_STAGING_APPROVED", "true")
    monkeypatch.setenv("SONNY_MCP_PUBLIC_RESOURCE_URL", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONNY_MCP_OAUTH_AUDIENCE", "https://different.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_PUBLIC_KEY_PEM", public)
    with pytest.raises(ValueError, match="audience"):
        create_staging_app()


def test_staging_rejects_non_mcp_resource_path(monkeypatch):
    monkeypatch.setenv("SONNY_MCP_STAGING_APPROVED", "true")
    monkeypatch.setenv("SONNY_MCP_PUBLIC_RESOURCE_URL", "https://sonny.example/other")
    with pytest.raises(ValueError, match="end with /mcp"):
        create_staging_app()


def test_main_rejects_invalid_port_before_loading_oauth_config(monkeypatch):
    from sonny.mcp_staging_entrypoint import main

    monkeypatch.setenv("PORT", "0")
    monkeypatch.setenv("SONNY_MCP_STAGING_APPROVED", "true")
    with pytest.raises(ValueError, match="PORT"):
        main()


def test_staging_builds_jwks_mode_without_pinned_key(monkeypatch):
    import asyncio
    import httpx

    monkeypatch.setenv("SONNY_MCP_STAGING_APPROVED", "true")
    monkeypatch.setenv("SONNY_MCP_AUTH_MODE", "jwks")
    monkeypatch.setenv("SONNY_MCP_PUBLIC_RESOURCE_URL", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONNY_MCP_OAUTH_AUDIENCE", "https://sonny.example/mcp")
    monkeypatch.setenv("SONNY_MCP_OAUTH_JWKS_URI", "https://issuer.example/keys")
    monkeypatch.delenv("SONNY_MCP_OAUTH_PUBLIC_KEY_PEM", raising=False)

    app = create_staging_app()

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
        ) as client:
            discovery = await client.get("/.well-known/oauth-protected-resource/mcp")
            assert discovery.status_code == 200
            assert discovery.json()["authorization_servers"] == ["https://issuer.example"]
            unauthorized = await client.get("/mcp")
            assert unauthorized.status_code == 401

    asyncio.run(run())
