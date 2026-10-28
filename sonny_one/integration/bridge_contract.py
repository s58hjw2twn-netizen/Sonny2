"""Fail-closed capability manifest for the proposed ChatGPT/Sonny ONE bridge.

This module is not a running MCP server or an authentication mechanism.
All capabilities are disabled until independently verified runtime gates exist.
"""
from __future__ import annotations

from copy import deepcopy

REPOSITORY = "s58hjw2twn-netizen/Sonny2"
RESEARCH_BRANCH = "research/apl-001"
SCHEMA_VERSION = 1

_CAPABILITIES = {
    "assistant.status": {"enabled": False, "effect": "read", "requires": ["authenticated_user", "authorized_runtime"]},
    "assistant.memory.read": {"enabled": False, "effect": "private_read", "requires": ["authenticated_user", "memory_consent", "authorized_runtime"]},
    "development.propose": {"enabled": False, "effect": "proposal", "requires": ["authenticated_user", "authorized_runtime"]},
    "development.validate": {"enabled": False, "effect": "isolated_execution", "requires": ["authenticated_controller", "sandbox_attestation", "trusted_evaluator"]},
    "development.commit": {"enabled": False, "effect": "repository_write", "requires": ["authenticated_controller", "exact_patch_digest", "trusted_evaluator", "branch_scoped_credentials"]},
    "development.merge_main": {"enabled": False, "effect": "forbidden", "requires": []},
    "development.deploy": {"enabled": False, "effect": "forbidden", "requires": []},
    "development.paid_model": {"enabled": False, "effect": "forbidden", "requires": []},
}


def capability_manifest() -> dict:
    """Return an independent snapshot, never a mutable shared policy."""
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": REPOSITORY,
        "research_branch": RESEARCH_BRANCH,
        "runtime_connected": False,
        "unattended_development_enabled": False,
        "capabilities": deepcopy(_CAPABILITIES),
    }


def authorize_capability(name: str, *, runtime_evidence: object = None) -> None:
    """Reject all runtime actions until a separately audited verifier exists.

    Caller-supplied evidence must never be trusted just because it is truthy.
    """
    if not isinstance(name, str) or name not in _CAPABILITIES:
        raise PermissionError("unknown bridge capability")
    raise PermissionError("Sonny ONE bridge runtime is not authenticated or activated")
