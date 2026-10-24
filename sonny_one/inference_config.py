"""Fail-closed inference configuration.

No provider secrets, network calls, or public endpoints are configured here.
External providers require a separate reviewed adapter and owner approval.
"""
from dataclasses import dataclass
from sonny_one.inference import OfflineProvider


class ProviderNotApproved(RuntimeError):
    """A real inference provider has not been approved."""


@dataclass(frozen=True)
class InferenceSettings:
    provider: str = "offline"
    allow_external: bool = False

    def __post_init__(self):
        if self.provider not in {"offline", "external"}:
            raise ValueError("Unknown inference provider")
        if not isinstance(self.allow_external, bool):
            raise ValueError("Invalid provider approval flag")


def build_provider(settings: InferenceSettings):
    if settings.provider == "offline":
        return OfflineProvider()
    raise ProviderNotApproved("External inference is not configured or approved")
