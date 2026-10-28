"""Security constraints for future MCP protected-resource discovery metadata."""
import pytest
from sonny.mcp_oauth_metadata import protected_resource_metadata


def test_valid_protected_resource_metadata():
    data = protected_resource_metadata(
        "https://sonny.example/mcp", "https://login.example"
    )
    assert data["resource"] == "https://sonny.example/mcp"
    assert data["authorization_servers"] == ["https://login.example"]
    assert data["scopes_supported"] == ["sonny.status.read"]
    assert data["bearer_methods_supported"] == ["header"]


@pytest.mark.parametrize("resource,issuer", [
    ("http://sonny.example/mcp", "https://login.example"),
    ("https://sonny.example/other", "https://login.example"),
    ("https://sonny.example/mcp?token=secret", "https://login.example"),
    ("https://sonny.example/mcp", "http://login.example"),
    ("https://sonny.example/mcp", "https://user:pass@login.example"),
    ("https://sonny.example/mcp", "https://login.example/tenant"),
])
def test_reject_untrusted_discovery_configuration(resource, issuer):
    with pytest.raises(ValueError):
        protected_resource_metadata(resource, issuer)
