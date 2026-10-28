"""Sonny ONE development agent: bounded, fail-closed task execution.

An explicit, injected coding adapter is required. This module does not run
untrusted shell commands, acquire credentials, or start background processes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sonny_one.development_controller.controller import plan, validate_queue


@dataclass(frozen=True)
class AgentResult:
    task_id: str | None
    status: str
    detail: str
    tasks_completed: int


class DevelopmentAgent:
    """Run a bounded sequence with a caller-supplied, trusted task executor.

    The executor must return True only after independently verified tests and
    successful commit. A False result stops without advancing the queue.
    """

    def __init__(self, executor: Callable[[dict], bool] | None = None):
        self.executor = executor

    def run(self, queue: dict, *, max_tasks: int = 1,
            authorized: bool = False) -> AgentResult:
        validate_queue(queue)
        if type(max_tasks) is not int or not 1 <= max_tasks <= 10:
            raise ValueError("max_tasks must be between 1 and 10")
        if not authorized:
            return AgentResult(None, "blocked", "explicit execution authorization required", 0)
        if self.executor is None:
            return AgentResult(None, "blocked", "no coding executor connected", 0)
        completed = 0
        last_id = None
        for _ in range(max_tasks):
            next_task = plan(queue)["next_task"]
            if next_task is None:
                return AgentResult(last_id, "idle", "no approved ready tasks", completed)
            last_id = next_task["id"]
            try:
                verified = self.executor(dict(next_task))
            except Exception:
                return AgentResult(last_id, "failed", "executor failed; task remains ready", completed)
            if verified is not True:
                return AgentResult(last_id, "failed", "no verified successful commit; task remains ready", completed)
            # Only the exact approved task selected from the validated queue
            # may advance; the executor receives a shallow copy.
            next_task["state"] = "done"
            completed += 1
        return AgentResult(last_id, "limit_reached", "bounded run completed", completed)
