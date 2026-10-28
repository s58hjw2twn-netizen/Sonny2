"""Private, in-process ASGI MCP prototype.

For trusted local test harnesses only. Does not bind a network port, offer
OAuth, or implement production remote MCP session/transport semantics.
"""
from __future__ import annotations

import json

from sonny_one.integration.auth_gate import authorize_bearer
from sonny_one.integration.mcp_protocol import handle_message

MAX_BODY_BYTES = 65536


async def private_mcp_app(scope, receive, send, *, expected_token=None):
    if scope.get("type") != "http":
        return
    # Refuse cross-origin browser requests; remote hosting needs an explicit
    # trusted-origin policy and CSRF/DNS-rebinding review before activation.
    if any(
        isinstance(key, bytes) and key.lower() == b"origin"
        for key, _ in scope.get("headers", [])
    ):
        await _respond(send, 403, {"error": "origin_not_allowed"})
        return
    if not authorize_bearer(scope.get("headers", []), expected_token):
        await _respond(send, 401, {"error": "unauthorized"})
        return
    if scope.get("method") != "POST" or scope.get("path") != "/private/mcp":
        await _respond(send, 404, {"error": "not_found"})
        return
    # Reject ambiguous or unexpected content types before parsing JSON.
    content_types = [
        value for key, value in scope.get("headers", [])
        if isinstance(key, bytes) and key.lower() == b"content-type"
    ]
    if len(content_types) != 1 or content_types[0].split(b";", 1)[0].strip().lower() != b"application/json":
        await _respond(send, 415, {"error": "unsupported_media_type"})
        return
    body = bytearray()
    while True:
        event = await receive()
        if event.get("type") != "http.request":
            await _respond(send, 400, {"error": "invalid_request"})
            return
        chunk = event.get("body", b"")
        if not isinstance(chunk, bytes) or len(body) + len(chunk) > MAX_BODY_BYTES:
            await _respond(send, 413, {"error": "request_too_large"})
            return
        body.extend(chunk)
        if not event.get("more_body", False):
            break
    try:
        message = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        await _respond(send, 400, {"error": "invalid_json"})
        return
    response = handle_message(message)
    if response is None:
        await _respond(send, 202, {})
    else:
        await _respond(send, 200, response)


async def _respond(send, status, payload):
    body = json.dumps(payload, separators=(",", ":")).encode()
    await send({"type": "http.response.start", "status": status, "headers": [
        (b"content-type", b"application/json"),
        (b"cache-control", b"no-store"),
        (b"x-content-type-options", b"nosniff"),
    ]})
    await send({"type": "http.response.body", "body": body})
