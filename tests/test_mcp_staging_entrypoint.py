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
