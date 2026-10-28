"""Pure OAuth protected-resource metadata builder for a future HTTPS MCP deployment.

Does not start a server, issue tokens, or expose any network listener.
"""
from urllib.parse import urlsplit


def _https_origin(value: str, name: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonempty HTTPS URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")):
        raise ValueError(f"{name} must be an HTTPS origin without credentials, path, query or fragment")
    if parsed.port is not None and parsed.port != 443:
        raise ValueError(f"{name} must use the default HTTPS port")
    return value.rstrip("/")


def protected_resource_metadata(resource_url: str, authorization_server: str) -> dict:
    """Build RFC 9728-style metadata; validate trusted operator-supplied URLs."""
    if not isinstance(resource_url, str):
        raise ValueError("resource URL must be a string")
    parsed_resource = urlsplit(resource_url)
    origin_candidate = f"{parsed_resource.scheme}://{parsed_resource.netloc}"
    origin = _https_origin(origin_candidate, "resource origin")
    if resource_url != origin + "/mcp":
        raise ValueError("resource URL must be the exact HTTPS /mcp endpoint")
    issuer = _https_origin(authorization_server, "authorization server")
    return {
        "resource": resource_url,
        "authorization_servers": [issuer],
        "scopes_supported": ["sonny.status.read"],
        "bearer_methods_supported": ["header"],
    }
