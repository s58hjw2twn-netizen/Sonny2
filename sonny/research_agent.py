"""Bounded Sonny research agent planner.

This module does not execute shell commands, write files, call models, or
make network requests. It produces reviewable, deterministic proposals.
Execution is a separate, explicitly gated component.
"""
from dataclasses import dataclass
from pathlib import PurePosixPath

ALLOWED_ROOTS = ("sonny/", "tests/", "docs/")
PROTECTED_PREFIXES = (".github/", "evaluation/", "benchmarks/", "frozen/")
MAX_TASKS = 8


@dataclass(frozen=True)
class Task:
    task_id: str
    objective: str
    paths: tuple[str, ...]
    risk: str = "low"


def validate_task(task: Task) -> None:
    if not task.task_id or not task.objective.strip():
        raise ValueError("task identifier and objective required")
    if task.risk not in {"low", "medium", "high"}:
        raise ValueError("unsupported risk classification")
    if not task.paths:
        raise ValueError("at least one target path required")
    for path in task.paths:
        normalized = PurePosixPath(path)
        if (
            not path or path.startswith("/") or "\\" in path
            or ".." in normalized.parts or "//" in path or str(normalized) != path
            or path.startswith(PROTECTED_PREFIXES)
            or not path.startswith(ALLOWED_ROOTS)
        ):
            raise ValueError(f"path not permitted: {path}")


def plan(tasks: list[Task]) -> dict:
    if not tasks or len(tasks) > MAX_TASKS:
        raise ValueError("task count outside allowed bounds")
    seen = set()
    proposed = []
    for task in tasks:
        validate_task(task)
        if task.task_id in seen:
            raise ValueError("duplicate task identifier")
        seen.add(task.task_id)
        proposed.append({
            "id": task.task_id,
            "objective": task.objective,
            "paths": list(task.paths),
            "risk": task.risk,
            "status": "PROPOSED",
            "execution_allowed": False,
        })
    return {
        "agent": "sonny-one-research",
        "mode": "plan-only",
        "tasks": proposed,
        "writes_performed": 0,
        "model_calls": 0,
    }
