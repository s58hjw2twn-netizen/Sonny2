"""Verify public OAuth discovery does not bypass the protected MCP boundary."""
import asyncio
import httpx
from sonny.mcp_oauth_discovery import ProtectedResourceDiscovery
from sonny.mcp_oauth_metadata import protected_resource_metadata


def test_discovery_is_public_and_other_paths_stay_protected():
    metadata = protected_resource_metadata("https://sonny.example/mcp", "https://login.example")

    async def protected(scope, receive, send):
        await send({"type": "http.response.start", "status": 401, "headers": []})
        await send({"type": "http.response.body", "body": b"blocked"})

    async def run():
        app = ProtectedResourceDiscovery(protected, metadata)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
        ) as client:
            for path in (
                "/.well-known/oauth-protected-resource",
                "/.well-known/oauth-protected-resource/mcp",
            ):
                response = await client.get(path)
                assert response.status_code == 200
                assert response.json() == metadata
                assert response.headers["cache-control"] == "no-store"
                assert (await client.post(path)).status_code == 405
            for path in ("/mcp", "/", "/.well-known/oauth-authorization-server"):
                response = await client.get(path)
                assert response.status_code == 401
                assert response.text == "blocked"

    asyncio.run(run())
