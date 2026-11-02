"""Explicit, fail-closed selection of approved local speech engines.

This module does not download weights, open sockets, or execute providers.
An engine must be separately installed, licensed, reviewed, and approved.
"""
from dataclasses import dataclass
from typing import Protocol


class DuplexEngine(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def cancel_output(self) -> None: ...


@dataclass(frozen=True)
class VoiceEngineOption:
    name: str
    engine: DuplexEngine
    approved: bool = False
    license_verified: bool = False
    locally_available: bool = False
    external_network_required: bool = False


class VoiceEngineRegistry:
    def __init__(self, options: list[VoiceEngineOption]):
        names = [item.name for item in options]
        if any(not name or not name.strip() for name in names):
            raise ValueError("engine name required")
        if len(set(names)) != len(names):
            raise ValueError("duplicate engine")
        self._options = {item.name: item for item in options}

    def select(self, name: str) -> DuplexEngine:
        option = self._options.get(name)
        if option is None:
            raise LookupError("unknown voice engine")
        if not (option.approved and option.license_verified and
                option.locally_available and not option.external_network_required):
            raise PermissionError("voice engine not approved for local use")
        return option.engine
