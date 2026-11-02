"""Fail-closed, proposal-only strategy switching for verified task outcomes.

No code execution, permissions, model calls, or automatic promotion occurs here.
"""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Attempt:
    task_family: str
    strategy: str
    succeeded: bool
    verified: bool
    evidence_id: str


@dataclass(frozen=True)
class SwitchDecision:
    status: str
    candidate: str | None
    reason: str


def propose_switch(attempts: Iterable[Attempt], *, task_family: str,
                   current_strategy: str, approved_alternatives: Iterable[str],
                   failure_threshold: int = 2) -> SwitchDecision:
    """Suggest an approved alternative after consecutive independently verified failures.

    Only an approved alternative with a verified successful historical attempt
    may be proposed. Unverified attempts reset the consecutive-failure chain;
    missing evidence cannot be used to justify a strategy change.
    """
    if not task_family or not current_strategy or type(failure_threshold) is not int or failure_threshold < 2:
        raise ValueError("invalid strategy request")
    history = list(attempts)
    if any(not isinstance(item, Attempt) for item in history):
        raise TypeError("attempts must contain Attempt records")
    relevant = [a for a in history if a.task_family == task_family]
    consecutive = 0
    for a in reversed(relevant):
        if a.strategy != current_strategy:
            continue
        if not a.verified or not a.evidence_id.strip() or a.succeeded:
            break
        consecutive += 1
    if consecutive < failure_threshold:
        return SwitchDecision("retain", None, "insufficient consecutive verified failures")
    alternatives = list(approved_alternatives)
    if any(not isinstance(s, str) or not s.strip() for s in alternatives):
        raise ValueError("invalid approved alternatives")
    for alternative in dict.fromkeys(alternatives):
        if alternative == current_strategy:
            continue
        if any(a.strategy == alternative and a.succeeded and a.verified and a.evidence_id.strip()
               for a in relevant):
            return SwitchDecision("proposal_only", alternative, "verified failures and approved evidenced alternative")
    return SwitchDecision("blocked", None, "no approved alternative with verified success evidence")
