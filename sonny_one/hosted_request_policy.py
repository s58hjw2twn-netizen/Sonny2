"""Conservative HTTP request checks for a future hosted deployment.

Pure functions only: not connected to a public ASGI app. The hosting proxy must
strip untrusted forwarding headers and supply verified TLS termination.
"""
from urllib.parse import urlsplit

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

def validate_hosted_request(*, canonical_origin: str, host: str | None,
                            origin: str | None, method: str,
                            verified_https: bool) -> None:
    """Reject requests that do not match the approved HTTPS origin.

    verified_https MUST come from trusted server/proxy configuration, never
    directly from an untrusted X-Forwarded-Proto request header.
    """
    expected = urlsplit(canonical_origin)
    if expected.scheme != "https" or not expected.hostname or expected.port is not None:
        raise ValueError("Invalid configured HTTPS origin")
    if not verified_https:
        raise PermissionError("Verified HTTPS required")
    if host != expected.netloc:
        raise PermissionError("Unexpected Host")
    if not isinstance(method, str) or method.upper() != method:
        raise PermissionError("Invalid method")
    if method not in SAFE_METHODS and origin != canonical_origin:
        raise PermissionError("Exact Origin required for state-changing requests")
    if origin is not None and origin != canonical_origin:
        raise PermissionError("Cross-origin browser request rejected")
