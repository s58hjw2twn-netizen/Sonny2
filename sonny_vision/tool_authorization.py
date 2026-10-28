"""Pre-execution tool authorization: deny unsafe methods before any side effects.

This gate must be invoked by a trusted orchestrator, not candidate code.
"""
from dataclasses import dataclass
from sonny_vision.assurance import AssuranceError


@dataclass(frozen=True)
class ToolCapability:
    name: str
    exact_region_edit: bool
    preserves_outside_mask: bool
    independent_postcheck: bool


@dataclass(frozen=True)
class TaskPolicy:
    task_type: str
    allowed_methods: tuple
    requires_exact_edit: bool = True
    requires_reference: bool = True


def authorize_tool(policy, tool, ledger, *, reference_id=None):
    """Fail closed for unknown methods, missing references or repeat failures."""
    if not policy.task_type or not policy.allowed_methods:
        raise AssuranceError("Task type and explicit allowlist required")
    if tool.name not in policy.allowed_methods:
        return {"status": "denied", "reason": "method_not_allowlisted"}
    if tool.name in ledger.blocked_methods(policy.task_type):
        return {"status": "denied", "reason": "repeated_failure"}
    if policy.requires_reference and not reference_id:
        return {"status": "denied", "reason": "missing_authoritative_reference"}
    if policy.requires_exact_edit and not (
        tool.exact_region_edit and tool.preserves_outside_mask
        and tool.independent_postcheck
    ):
        return {"status": "denied", "reason": "cannot_enforce_preservation"}
    return {"status": "authorized", "reason": "preflight_passed"}


def execute_authorized(policy, tool, ledger, operation, *, reference_id=None):
    """Invoke an operation only after the preflight gate allows it.

    Does not replace OS sandboxing, filesystem permission checks, or postchecks.
    """
    decision = authorize_tool(policy, tool, ledger, reference_id=reference_id)
    if decision["status"] != "authorized":
        raise AssuranceError("Tool execution blocked: " + decision["reason"])
    return operation()
