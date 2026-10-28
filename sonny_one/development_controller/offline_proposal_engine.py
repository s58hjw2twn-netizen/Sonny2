"""First offline code-proposal engine for Sonny ONE's development agent.

Reuses the existing deterministic APL proposal generator and disposable
applicability checks. Produces review-only patches, never executes or commits
them. This is not an LLM coding engine or autonomous development.
"""
from __future__ import annotations

from pathlib import Path

from sonny_one.apl.package import prepare_bundle


class OfflineProposalEngine:
    def __init__(self, source: str | Path, *, max_candidates: int = 1):
        if type(max_candidates) is not int or not 1 <= max_candidates <= 3:
            raise ValueError("candidate budget must be 1..3")
        self.source = Path(source)
        self.max_candidates = max_candidates
        self.last_bundle: dict | None = None

    def propose(self, task: dict) -> dict:
        if not isinstance(task, dict) or task.get("id") != "RES-001":
            raise PermissionError("offline generator only supports research task RES-001")
        if task.get("state") != "ready" or task.get("requires_approval") is not False:
            raise PermissionError("task is not authorized")
        bundle = prepare_bundle(self.source, max_candidates=self.max_candidates)
        self.last_bundle = bundle
        return {"task_id": task["id"], "proposal_count": len(bundle["proposals"]),
                "bundle": bundle, "committed": False,
                "tests_executed": False, "development_task_completed": False}

    def __call__(self, task: dict) -> bool:
        self.propose(task)
        # A generated patch is not a tested and verified commit.
        return False
