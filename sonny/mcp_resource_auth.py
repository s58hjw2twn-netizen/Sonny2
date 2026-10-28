"""Standalone OAuth resource-token verifier (NOT wired to the MCP server).

Requires an administrator-configured trusted issuer, audience and pinned
RSA public key. Does not issue tokens, discover keys, or authorize any tool.
Do not expose an MCP endpoint until this verifier is integrated and tested.
"""
from dataclasses import dataclass
import jwt


class TokenRejected(ValueError):
    """A bearer token failed resource-server verification."""


@dataclass(frozen=True)
class ResourceAuthConfig:
    issuer: str
    audience: str
    public_key_pem: str
    required_scope: str = "sonny.status.read"

    def __post_init__(self):
        if not all((self.issuer, self.audience, self.public_key_pem, self.required_scope)):
            raise ValueError("All OAuth resource authorization settings are required")
        if not self.issuer.startswith("https://") or not self.audience.startswith("https://"):
            raise ValueError("Issuer and audience must use HTTPS")


def verify_resource_token(token: str, config: ResourceAuthConfig) -> dict:
    """Validate RS256 signature, issuer, audience, expiry, and required scope."""
    if not isinstance(token, str) or not token or len(token) > 8192:
        raise TokenRejected("Invalid bearer token")
    try:
        claims = jwt.decode(
            token,
            config.public_key_pem,
            algorithms=["RS256"],
            issuer=config.issuer,
            audience=config.audience,
            options={"require": ["iss", "aud", "exp", "iat", "sub"]},
            leeway=0,
        )
    except jwt.PyJWTError as exc:
        raise TokenRejected("Invalid bearer token") from exc
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise TokenRejected("Invalid subject")
    scope = claims.get("scope", "")
    if not isinstance(scope, str) or config.required_scope not in scope.split():
        raise TokenRejected("Insufficient scope")
    return claims
