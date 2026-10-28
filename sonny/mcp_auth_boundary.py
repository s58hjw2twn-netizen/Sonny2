"""Fail-closed ASGI bearer-token boundary for a *local-only* MCP prototype.

This is not an OAuth authorization server or a deployable ChatGPT connector.
It never logs tokens and must not be used as a public service.
"""
from sonny.mcp_resource_auth import TokenRejected, verify_resource_token


class BearerAuthBoundary:
    def __init__(self, app, config, resource_metadata_url=None):
        self.app = app
        self.config = config
        self.resource_metadata_url = resource_metadata_url

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        # All HTTP paths, including metadata and probes, require authorization.
        headers = [(k.lower(), v) for k, v in scope.get("headers", [])]
        auth_values = [v for k, v in headers if k == b"authorization"]
        authorized = False
        if len(auth_values) == 1:
            try:
                scheme, token = auth_values[0].decode("ascii").split(" ", 1)
                if scheme.lower() == "bearer" and token and token.strip() == token:
                    verify_resource_token(token, self.config)
                    authorized = True
            except (UnicodeDecodeError, ValueError, TokenRejected):
                pass
        if not authorized:
            body = b'{"error":"unauthorized"}'
            challenge = 'Bearer error="invalid_token"'
            if self.resource_metadata_url is not None:
                challenge += f', resource_metadata="{self.resource_metadata_url}"'
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"no-store"),
                    (b"www-authenticate", challenge.encode("ascii")),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)
