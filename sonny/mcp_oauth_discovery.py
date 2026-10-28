"""Read-only RFC 9728 discovery wrapper for local integration tests.

This wrapper does not issue tokens, create an OAuth server, or deploy a service.
Place it *outside* the bearer boundary so unauthenticated clients can discover
the authorization server. All other requests pass through unchanged.
"""
import json

DISCOVERY_PATHS = frozenset({
    "/.well-known/oauth-protected-resource",
    "/.well-known/oauth-protected-resource/mcp",
})


class ProtectedResourceDiscovery:
    def __init__(self, app, metadata: dict):
        self.app = app
        self.payload = json.dumps(metadata, separators=(",", ":")).encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("path") not in DISCOVERY_PATHS:
            await self.app(scope, receive, send)
            return
        if scope.get("method") != "GET":
            await send({
                "type": "http.response.start", "status": 405,
                "headers": [(b"allow", b"GET"), (b"cache-control", b"no-store")],
            })
            await send({"type": "http.response.body", "body": b""})
            return
        await send({
            "type": "http.response.start", "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"cache-control", b"no-store"),
                (b"content-length", str(len(self.payload)).encode("ascii")),
            ],
        })
        await send({"type": "http.response.body", "body": self.payload})
