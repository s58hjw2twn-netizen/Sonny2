"""Strict review gate for proposed coding-runner execution.

A task handoff is never an authorization. This function can only validate a
separate, explicit execution grant supplied by a trusted controller. It does
not execute code, grant credentials, or mutate a repository.
"""
from __future__ import annotations

from sonny_one.development_controller.handoff import ALLOWED_BRANCH


def validate_execution_grant(handoff: dict, grant: dict) -> dict:
    if not isinstance(handoff, dict) or not isinstance(grant, dict):
        raise ValueError("handoff and grant must be objects")
    task = handoff.get("task")
    if not isinstance(task, dict) or not isinstance(task.get("id"), str):
        raise PermissionError("no eligible task")
    if handoff.get("mode") != "proposal_only":
        raise PermissionError("invalid handoff mode")
    if handoff.get("branch") != ALLOWED_BRANCH:
        raise PermissionError("unexpected target branch")
    if handoff.get("repository") != "s58hjw2twn-netizen/Sonny2":
        raise PermissionError("unexpected repository")
    expected_keys = {"task_id", "branch", "sandbox_verified", "credential_scope_verified",
                     "owner_policy_verified", "paid_services_enabled",
                     "production_deploy_enabled", "merge_main_enabled"}
    if set(grant) != expected_keys:
        raise PermissionError("invalid grant schema")
    if grant["task_id"] != task["id"] or grant["branch"] != ALLOWED_BRANCH:
        raise PermissionError("task or branch mismatch")
    for key in ("sandbox_verified", "credential_scope_verified", "owner_policy_verified"):
        if grant[key] is not True:
            raise PermissionError("missing independent execution safeguard")
    for key in ("paid_services_enabled", "production_deploy_enabled", "merge_main_enabled"):
        if grant[key] is not False:
            raise PermissionError("prohibited external effect")
    return {"task_id": task["id"], "branch": ALLOWED_BRANCH,
            "review_gate_passed": True, "execution_started": False,
            "grant_authenticity_verified": False,
            "credentials_provided": False}


def runner_available() -> bool:
    """Never claim a coding runner is connected based on static repository files."""
    return False
