"""Fail-closed configuration validation for a future hosted Sonny ONE app.

This does not create a public server or relax the local pilot boundary.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

@dataclass(frozen=True)
class HostedConfig:
    origin: str
    database_url: str
    auth_secret: str

    def validate(self) -> None:
        parsed = urlsplit(self.origin)
        if (parsed.scheme != "https" or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or parsed.port is not None):
            raise ValueError("Hosted origin must be a canonical HTTPS hostname")
        if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("Hosted origin cannot be loopback")
        if not self.database_url.strip():
            raise ValueError("Persistent database configuration required")
        if len(self.auth_secret) < 48:
            raise ValueError("A separate strong hosted signing secret is required")

def require_hosted_configuration(config: HostedConfig) -> HostedConfig:
    """Validate before any hosted server can be constructed."""
    config.validate()
    return config
