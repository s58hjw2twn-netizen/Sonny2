"""ASGI enforcement wrapper for a future hosted application.

Not a deployment entry point. verified_tls must come from trusted deployment
configuration, never from client-supplied forwarding headers.
"""
from sonny_one.hosted_request_policy import validate_hosted_request

class HostedRequestBoundary:
    def __init__(self, app, *, canonical_origin: str, verified_tls: bool = False):
        self.app = app
        self.canonical_origin = canonical_origin
        self.verified_tls = verified_tls

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # No WebSocket functionality is authorized for the hosted pilot.
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            await self.app(scope, receive, send)
            return
        headers = scope.get("headers", [])
        hosts = [v.decode("latin1") for k, v in headers if k.lower() == b"host"]
        origins = [v.decode("latin1") for k, v in headers if k.lower() == b"origin"]
        try:
            if len(hosts) != 1 or len(origins) > 1:
                raise PermissionError("Ambiguous host or origin")
            validate_hosted_request(
                canonical_origin=self.canonical_origin,
                host=hosts[0], origin=origins[0] if origins else None,
                method=scope.get("method", ""), verified_https=self.verified_tls)
        except (PermissionError, ValueError):
            await send({"type": "http.response.start", "status": 403,
                        "headers": [(b"content-type", b"text/plain"),
                                    (b"cache-control", b"no-store")]})
            await send({"type": "http.response.body", "body": b"Forbidden"})
            return
        await self.app(scope, receive, send)
