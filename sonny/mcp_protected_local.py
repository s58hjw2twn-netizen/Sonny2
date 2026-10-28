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

HOST = "127.0.0.1"
PORT = 8766

mcp = FastMCP(
    "Sonny ONE Protected Local MCP",
    host=HOST,
    port=PORT,
    json_response=True,
    stateless_http=True,
)

@mcp.tool()
def protocol_status() -> dict[str, str]:
    """Read-only, non-sensitive MCP readiness status."""
    return {"service": "Sonny ONE", "mode": "protected-local",
            "production_ready": "false"}


def build_app(config: ResourceAuthConfig, *, resource_url: str | None = None):
    """Wrap MCP with bearer auth; optionally publish read-only OAuth discovery.

    The resource URL is an operator-supplied HTTPS identifier, not a listener
    configuration. Discovery does not make the loopback server remotely usable.
    """
    protected = BearerAuthBoundary(mcp.streamable_http_app(), config)
    if resource_url is None:
        return protected
    metadata = protected_resource_metadata(resource_url, config.issuer)
    if resource_url != config.audience:
        raise ValueError("OAuth resource URL must match the JWT audience")
    return ProtectedResourceDiscovery(protected, metadata)


def config_from_environment() -> ResourceAuthConfig:
    return ResourceAuthConfig(
        issuer=os.environ["SONNY_MCP_OAUTH_ISSUER"],
        audience=os.environ["SONNY_MCP_OAUTH_AUDIENCE"],
        public_key_pem=os.environ["SONNY_MCP_OAUTH_PUBLIC_KEY_PEM"],
    )


if __name__ == "__main__":
    import uvicorn
    # Fail before binding if any authentication setting is absent or invalid.
    app = build_app(
        config_from_environment(),
        resource_url=os.environ.get("SONNY_MCP_PUBLIC_RESOURCE_URL"),
    )
    uvicorn.run(app, host=HOST, port=PORT)
