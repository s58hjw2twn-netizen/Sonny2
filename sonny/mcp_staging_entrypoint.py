"""Explicit, fail-closed staging entrypoint; not enabled by Dockerfile.mcp.

Requires operator confirmation of OAuth provider integration and deployment
security review before any public network listener is started.
"""
import os

from sonny.mcp_protected_local import build_app, config_from_environment


def create_staging_app():
    if os.environ.get("SONNY_MCP_STAGING_APPROVED") != "true":
        raise RuntimeError("MCP staging requires explicit approval")
    resource_url = os.environ["SONNY_MCP_PUBLIC_RESOURCE_URL"]
    config = config_from_environment()
    return build_app(config, resource_url=resource_url)


def main():
    # No network listener is started unless all required settings validate.
    app = create_staging_app()
    port = int(os.environ.get("PORT", "8000"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
