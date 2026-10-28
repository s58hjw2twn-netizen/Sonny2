"""Explicitly injected private inference provider; never auto-connects external AI.

A reviewed deployment can install a provider at application startup. The
default is always the offline adapter; importing this module makes no calls.
"""
from threading import Lock
from sonny_one.inference import OfflineProvider, Provider

_lock = Lock()
_provider: Provider = OfflineProvider()


def get_private_provider() -> Provider:
    with _lock:
        return _provider


def install_private_provider(provider: Provider, *, approved: bool = False) -> None:
    if approved is not True:
        raise PermissionError("External provider activation requires explicit approval")
    if provider is None or not callable(getattr(provider, "generate", None)):
        raise TypeError("Invalid provider")
    global _provider
    with _lock:
        _provider = provider


def reset_private_provider() -> None:
    global _provider
    with _lock:
        _provider = OfflineProvider()
