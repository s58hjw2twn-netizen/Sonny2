"""Non-deployable hosted application assembly for integration tests.

This module deliberately does not expose authentication, memory, or chat yet.
It fails closed until a separately reviewed hosted backend is implemented.
"""
from sonny_one.hosted_config import HostedConfig, require_hosted_configuration
from sonny_one.hosted_boundary import HostedRequestBoundary

async def unavailable_app(scope, receive, send):
    if scope["type"] != "http":
        return
    await send({"type": "http.response.start", "status": 503,
                "headers": [(b"content-type", b"application/json"),
                            (b"cache-control", b"no-store")]})
    await send({"type": "http.response.body",
                "body": b'{"status":"not_ready","model_connected":false}'})

def build_hosted_candidate(config: HostedConfig, *, trusted_tls: bool = False):
    """Return a deny-by-default candidate, never the local pilot app.

    trusted_tls is deliberately false by default. A verified deployment
    configuration must explicitly provide it after a security review.
    """
    require_hosted_configuration(config)
    return HostedRequestBoundary(unavailable_app,
                                 canonical_origin=config.origin,
                                 verified_tls=trusted_tls)
