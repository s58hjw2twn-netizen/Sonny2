"""Offline checks for operator-supplied OAuth provider metadata."""
from urllib.parse import urlsplit


def validate_provider(metadata, expected_issuer):
    """Validate required HTTPS endpoints and OAuth code + PKCE S256 support."""
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    if not isinstance(expected_issuer, str) or metadata.get("issuer") != expected_issuer:
        raise ValueError("issuer mismatch")
    urls = {
        "issuer": expected_issuer,
        "authorization_endpoint": metadata.get("authorization_endpoint"),
        "token_endpoint": metadata.get("token_endpoint"),
        "jwks_uri": metadata.get("jwks_uri"),
    }
    for label, value in urls.items():
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError(f"{label} must be an HTTPS URL")
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.fragment):
            raise ValueError(f"{label} must be an HTTPS URL without credentials or fragment")
    if "code" not in metadata.get("response_types_supported", []):
        raise ValueError("authorization code required")
    if "S256" not in metadata.get("code_challenge_methods_supported", []):
        raise ValueError("PKCE S256 required")
    return urls
