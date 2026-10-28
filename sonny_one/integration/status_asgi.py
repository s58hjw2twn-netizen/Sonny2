"""Read-only Sonny ONE bridge ASGI application.

Deliberately separate from the personal-memory and development runtimes.
No credentials, sessions, repository writes, or actions are exposed here.
This is a prototype, not an authenticated production MCP endpoint.
"""
from __future__ import annotations

import json

from sonny_one.integration.bridge_contract import read_public_bridge_status


async def app(scope, receive, send):
    if scope["type"] != "http":
        return
    method = scope.get("method", "GET")
    path = scope.get("path", "")
    if method == "GET" and path == "/health":
        status, payload = 200, {"service": "sonny-one-bridge", "healthy": True}
    elif method == "GET" and path == "/v1/public/status":
        status, payload = 200, read_public_bridge_status()
    else:
        status, payload = 404, {"error": "not_found"}
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    await send({
        "type": "http.response.start", "status": status,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"),
            (b"referrer-policy", b"no-referrer"),
        ],
    })
    await send({"type": "http.response.body", "body": body})
