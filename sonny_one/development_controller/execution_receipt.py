"""Validate externally produced development receipts without executing code.

This is an evidence gate, not a GitHub verifier. The trusted orchestrator
must independently obtain CI status and commit identity from GitHub and
supply them here. Caller-provided strings alone are not proof.
"""
from __future__ import annotations

import re

_SHA = re.compile(r"^[0-9a-f]{40}$")
_RUN = re.compile(r"^[1-9][0-9]{0,19}$")
_ALLOWED_BRANCH = "research/apl-001"


def validate_execution_receipt(receipt: dict, *, expected_task_id: str,
                               expected_parent_sha: str) -> dict:
    if not isinstance(receipt, dict):
        raise ValueError("invalid receipt")
    required = {"task_id", "parent_sha", "commit_sha", "branch",
                "test_run_id", "test_conclusion", "policy_run_id",
                "policy_conclusion", "independent_verification"}
    if set(receipt) != required:
        raise ValueError("unexpected receipt fields")
    if not isinstance(expected_task_id, str) or not expected_task_id:
        raise ValueError("invalid task id")
    if not isinstance(expected_parent_sha, str) or not _SHA.fullmatch(expected_parent_sha):
        raise ValueError("invalid expected parent")
    if receipt["task_id"] != expected_task_id:
        raise ValueError("task mismatch")
    if receipt["parent_sha"] != expected_parent_sha:
        raise ValueError("parent mismatch")
    if receipt["branch"] != _ALLOWED_BRANCH:
        raise ValueError("branch not permitted")
    commit = receipt["commit_sha"]
    if not isinstance(commit, str) or not _SHA.fullmatch(commit) or commit == expected_parent_sha:
        raise ValueError("invalid commit")
    for field in ("test_run_id", "policy_run_id"):
        value = receipt[field]
        if not isinstance(value, str) or not _RUN.fullmatch(value):
            raise ValueError("invalid workflow run id")
    if receipt["test_run_id"] == receipt["policy_run_id"]:
        raise ValueError("independent checks require distinct runs")
    if receipt["test_conclusion"] != "success" or receipt["policy_conclusion"] != "success":
        raise ValueError("required checks did not pass")
    if receipt["independent_verification"] is not True:
        raise ValueError("trusted external verification required")
    return {"accepted_shape": True, "task_id": expected_task_id,
            "commit_sha": commit, "independently_verified_by_this_module": False}
