"""Local-only MCP protocol spike. NOT an authenticated production connector.

Run after installing pinned mcp v1 dependency:
    python -m pip install "mcp>=1.28,<2"
    python -m sonny.mcp_local_spike

This binds ONLY to 127.0.0.1. Never expose this listener through a tunnel,
reverse proxy, container port publishing, or public network. It provides
only static, non-sensitive metadata and no GitHub or application access.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Sonny ONE Local Protocol Spike",
    host="127.0.0.1",
    port=8765,
    json_response=True,
    stateless_http=True,
)

@mcp.tool()
def protocol_status() -> dict[str, str]:
    """Return non-sensitive static protocol-spike metadata."""
    return {
        "service": "Sonny ONE",
        "mode": "local-protocol-spike",
        "authentication": "not-configured",
        "production_ready": "false",
    }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
