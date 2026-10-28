"""Sonny ONE capability inventory: declarative, conservative, and auditable.

This file lists roadmap capabilities and does NOT probe or enable integrations.
Do not turn a planned capability into an enabled one without runtime evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    status: str
    evidence: str
    requires_approval: bool = False


CAPABILITIES = (
    Capability("personal_memory", "prototype", "sonny_one/life_memory.py; sonny_one/memory_policy.py"),
    Capability("integrity_self_check", "prototype", "sonny_one/assistant.py; sonny_one/apl/"),
    Capability("voice_personality", "planned", "No verified voice input/output integration"),
    Capability("sonny_vision", "prototype", "sonny_vision/identity/geometry_gate.py; sonny_vision/restoration/face_protection.py"),
    Capability("personal_agent", "planned", "No approved general-purpose external-action executor", True),
    Capability("creative_studio", "planned", "No verified media production runtime", True),
)


def capability_inventory() -> list[dict]:
    return [asdict(capability) for capability in CAPABILITIES]


def capability_status(name: str) -> dict:
    for capability in CAPABILITIES:
        if capability.name == name:
            return asdict(capability)
    raise KeyError("unknown capability")


def execution_allowed(name: str) -> bool:
    """No capability is authorized to execute external actions by this inventory."""
    capability_status(name)
    return False
