"""Authenticated MCP *loopback-only* ASGI application.

Requires an externally managed OAuth issuer and pinned RS256 public key.
Not a complete OAuth discovery/authorization flow or production deployment.
Never expose this listener to the internet.
"""
import os
from mcp.server.fastmcp import FastMCP
from sonny.mcp_auth_boundary import BearerAuthBoundary
from sonny.mcp_oauth_discovery import ProtectedResourceDiscovery
from sonny.mcp_oauth_metadata import protected_resource_metadata
from sonny.mcp_resource_auth import ResourceAuthConfig
from sonny.mcp_jwks_auth import JwksAuthConfig, verify_jwks_resource_token

HOST = "127.0.0.1"
PORT = 8766

def create_mcp_server() -> FastMCP:
    """Create a fresh, single-use MCP session manager per application instance."""
    server = FastMCP(
        "Sonny ONE Protected Local MCP",
        host=HOST,
        port=PORT,
        json_response=True,
        stateless_http=True,
    )

    @server.tool()
    def protocol_status() -> dict[str, str]:
        """Read-only, non-sensitive MCP readiness status."""
        return {"service": "Sonny ONE", "mode": "protected-local",
                "production_ready": "false"}

    return server


def build_app(config: ResourceAuthConfig, *, resource_url: str | None = None,
              server: FastMCP | None = None, token_verifier=None):
    """Wrap a fresh MCP server with bearer auth and optional public discovery."""
    if resource_url is not None:
        metadata = protected_resource_metadata(resource_url, config.issuer)
        if resource_url != config.audience:
            raise ValueError("OAuth resource URL must match the JWT audience")
    else:
        metadata = None

    server = server if server is not None else create_mcp_server()
    discovery_url = (resource_url.removesuffix('/mcp') +
                     '/.well-known/oauth-protected-resource/mcp') if metadata else None
    protected = BearerAuthBoundary(server.streamable_http_app(), config,
                                   resource_metadata_url=discovery_url,
                                   token_verifier=token_verifier)
    if metadata is None:
        return protected
    return ProtectedResourceDiscovery(protected, metadata)


def config_from_environment():
    """Load an explicitly selected verifier mode from administrator settings."""
    mode = os.environ.get("SONNY_MCP_AUTH_MODE", "pinned_key")
    if mode == "jwks":
        config = JwksAuthConfig(
            issuer=os.environ["SONNY_MCP_OAUTH_ISSUER"],
            audience=os.environ["SONNY_MCP_OAUTH_AUDIENCE"],
            jwks_uri=os.environ["SONNY_MCP_OAUTH_JWKS_URI"],
        )
        return config, verify_jwks_resource_token
    if mode == "pinned_key":
        config = ResourceAuthConfig(
            issuer=os.environ["SONNY_MCP_OAUTH_ISSUER"],
            audience=os.environ["SONNY_MCP_OAUTH_AUDIENCE"],
            public_key_pem=os.environ["SONNY_MCP_OAUTH_PUBLIC_KEY_PEM"],
        )
        return config, None
    raise ValueError("SONNY_MCP_AUTH_MODE must be 'pinned_key' or 'jwks'")


if __name__ == "__main__":
    import uvicorn
    # Fail before binding if any authentication setting is absent or invalid.
    auth_config, token_verifier = config_from_environment()
    app = build_app(
        auth_config,
        resource_url=os.environ.get("SONNY_MCP_PUBLIC_RESOURCE_URL"),
        token_verifier=token_verifier,
    )
    uvicorn.run(app, host=HOST, port=PORT)
