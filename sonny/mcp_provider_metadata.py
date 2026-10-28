"""Offline checks for operator-supplied OAuth provider metadata."""
from urllib.parse import urlsplit


def validate_provider(metadata, expected_issuer):
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    if metadata.get("issuer") != expected_issuer:
        raise ValueError("issuer mismatch")
    for value in (expected_issuer, metadata.get("authorization_endpoint"), metadata.get("token_endpoint"), metadata.get("jwks_uri")):
        if not isinstance(value, str):
            raise ValueError("HTTPS provider URLs required")
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("HTTPS provider URLs required")
    if "code" not in metadata.get("response_types_supported", []):
        raise ValueError("authorization code required")
    if "S256" not in metadata.get("code_challenge_methods_supported", []):
        raise ValueError("PKCE S256 required")
    return {\n        "issuer": expected_issuer,\n        "authorization_endpoint": metadata["authorization_endpoint"],\n        "token_endpoint": metadata["token_endpoint"],\n        "jwks_uri": metadata["jwks_uri"],\n    }
