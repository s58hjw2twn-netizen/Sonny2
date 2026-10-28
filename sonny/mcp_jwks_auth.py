"""Isolated JWKS-backed OAuth resource-token verifier.

Not wired to the MCP server. Only use with an administrator-verified JWKS URL
and issuer. The HTTPS JWKS client is bounded by a short timeout.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

import jwt


class TokenRejected(ValueError):
    """A bearer token failed resource-server verification."""


@dataclass(frozen=True)
class JwksAuthConfig:
    issuer: str
    audience: str
    jwks_uri: str
    required_scope: str = "sonny.status.read"

    def __post_init__(self):
        if not all((self.issuer, self.audience, self.jwks_uri, self.required_scope)):
            raise ValueError("All JWKS authorization settings are required")
        for label, value in (("issuer", self.issuer), ("audience", self.audience), ("JWKS URI", self.jwks_uri)):
            parsed = urlsplit(value)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                raise ValueError(f"{label} must be an HTTPS URL without credentials or fragment")


def verify_jwks_resource_token(token: str, config: JwksAuthConfig) -> dict:
    """Verify RS256 token using keys fetched from a preconfigured trusted JWKS URI."""
    if not isinstance(token, str) or not token or len(token) > 8192:
        raise TokenRejected("Invalid bearer token")
    try:
        # Reject malformed or unsupported headers before any JWKS network lookup.
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            raise TokenRejected("Invalid bearer token")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid or len(kid) > 128:
            raise TokenRejected("Invalid bearer token")
        # Imported here to keep provider/network access isolated until invoked.
        from jwt import PyJWKClient
        client = PyJWKClient(config.jwks_uri, timeout=5, cache_keys=True)
        signing_key = client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=config.issuer,
            audience=config.audience,
            options={"require": ["iss", "aud", "exp", "iat", "sub"]},
            leeway=0,
        )
    except Exception as exc:
        # Never leak token contents, provider response bodies, or network details.
        raise TokenRejected("Invalid bearer token") from exc
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise TokenRejected("Invalid subject")
    scope = claims.get("scope", "")
    if not isinstance(scope, str) or config.required_scope not in scope.split():
        raise TokenRejected("Insufficient scope")
    return claims
