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


def validate_chatgpt_client_registration(metadata, *, mode="cimd"):
    """Fail closed if OAuth metadata does not advertise the requested client mode.

    This is an offline capability check, not proof of provider operability.
    A manually pre-registered client is configured outside this function.
    """
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    methods = metadata.get("token_endpoint_auth_methods_supported")
    if not isinstance(methods, list) or not all(isinstance(v, str) for v in methods):
        raise ValueError("token endpoint authentication methods must be advertised")
    if mode == "cimd":
        if metadata.get("client_id_metadata_document_supported") is not True:
            raise ValueError("CIMD must be advertised")
        acceptable = ("private_key_jwt", "none")
    elif mode == "dcr":
        registration_url = metadata.get("registration_endpoint")
        if not isinstance(registration_url, str):
            raise ValueError("DCR registration endpoint is required")
        parsed = urlsplit(registration_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.fragment):
            raise ValueError("DCR registration endpoint must use HTTPS")
        acceptable = ("none", "client_secret_post", "client_secret_basic")
    else:
        raise ValueError("Unsupported client registration mode")
    selected = next((method for method in acceptable if method in methods), None)
    if selected is None:
        raise ValueError("No supported token endpoint authentication method")
    return selected
