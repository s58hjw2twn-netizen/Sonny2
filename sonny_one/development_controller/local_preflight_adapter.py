"""Controlled local test adapter for Sonny ONE development.

This adapter only runs the fixed, offline validation commands already defined
by validation_runner. It cannot write code or commit changes. It never returns
the boolean True expected by DevelopmentAgent for a completed coding task.
"""
from __future__ import annotations

from sonny_one.development_controller.validation_runner import COMMANDS, execute_validation


def run_local_preflight(task: dict, *, validation: str = "controller",
                        timeout_seconds: int = 30) -> dict:
    if not isinstance(task, dict) or not isinstance(task.get("id"), str):
        raise ValueError("invalid task")
    if task.get("requires_approval") is not False or task.get("state") != "ready":
        raise PermissionError("task not approved for local preflight")
    if validation not in COMMANDS:
        raise ValueError("validation not allowlisted")
    result = execute_validation(validation, timeout_seconds)
    return {"task_id": task["id"], "validation": validation,
            "passed": result["passed"], "return_code": result["return_code"],
            "duration_seconds": result["duration_seconds"],
            "code_changes_made": False, "commit_created": False,
            "development_task_completed": False}


class LocalPreflightAdapter:
    """Callable adapter for testing the agent's fail-closed integration."""

    def __init__(self, validation: str = "controller"):
        if validation not in COMMANDS:
            raise ValueError("validation not allowlisted")
        self.validation = validation
        self.last_report: dict | None = None

    def __call__(self, task: dict) -> bool:
        self.last_report = run_local_preflight(task, validation=self.validation)
        # A passing test alone is never proof of new code or a verified commit.
        return False
