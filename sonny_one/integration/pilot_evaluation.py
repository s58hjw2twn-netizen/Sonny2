"""Privacy-minimal, deterministic Pilot 002 task ledger and scorecard.

No network, persistence, user identifiers or autonomous actions. The caller
owns retention, access control and consent. Unknown outcomes are never scored.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

Status = Literal["requested", "awaiting_input", "in_progress", "completed", "blocked"]
Verification = Literal["verified", "unverified", "unknown"]


@dataclass(frozen=True)
class TaskEvidence:
    task_id: str
    occurred_at: str
    category: str
    status: Status
    verification: Verification = "unknown"
    outcome: Literal["success", "failure", "unknown"] = "unknown"
    correction_count: int = 0
    user_accepted: bool | None = None

    def __post_init__(self) -> None:
        if not self.task_id or not self.category:
            raise ValueError("task_id and category are required")
        try:
            dt = datetime.fromisoformat(self.occurred_at.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError("occurred_at must be an ISO 8601 timestamp") from exc
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("occurred_at must include timezone")
        if self.status not in {"requested", "awaiting_input", "in_progress", "completed", "blocked"}:
            raise ValueError("invalid task status")
        if self.verification not in {"verified", "unverified", "unknown"}:
            raise ValueError("invalid verification")
        if self.outcome not in {"success", "failure", "unknown"}:
            raise ValueError("invalid outcome")
        if isinstance(self.correction_count, bool) or not isinstance(self.correction_count, int) or self.correction_count < 0:
            raise ValueError("invalid correction count")
        if self.user_accepted is not None and not isinstance(self.user_accepted, bool):
            raise ValueError("invalid user acceptance")
        if self.outcome != "unknown" and (self.status != "completed" or self.verification != "verified"):
            raise ValueError("scored outcomes require completed and independently verified tasks")


def scorecard(tasks: list[TaskEvidence]) -> dict:
    ids = [t.task_id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task IDs")
    statuses = Counter(t.status for t in tasks)
    verified = [t for t in tasks if t.status == "completed" and t.verification == "verified" and t.outcome != "unknown"]
    successes = sum(t.outcome == "success" for t in verified)
    return {
        "total_recorded": len(tasks),
        "status_counts": dict(statuses),
        "verified_scored": len(verified),
        "verified_successes": successes,
        "verified_failures": len(verified) - successes,
        "unknown_or_unverified": len(tasks) - len(verified),
        "verified_success_rate": successes / len(verified) if verified else None,
        "corrections_recorded": sum(t.correction_count for t in tasks),
        "coverage_note": "Rate covers only verified scored tasks, not all pilot requests.",
    }
