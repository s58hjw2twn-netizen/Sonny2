"""Deterministic memory admission and retrieval rules for research prototypes.

This module intentionally stores no user information and performs no model calls.
"""
from dataclasses import dataclass
from enum import Enum

class MemoryStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    QUARANTINED = "quarantined"
    RETIRED = "retired"

@dataclass(frozen=True)
class MemoryCandidate:
    user_id: str
    source: str
    statement: str
    status: MemoryStatus = MemoryStatus.PROPOSED
    confidence: float = 0.0
    consent: bool = False

def admission_decision(candidate: MemoryCandidate) -> str:
    if not candidate.user_id or not candidate.source or not candidate.statement:
        return "reject-incomplete"
    if not candidate.consent:
        return "reject-no-consent"
    if not 0 <= candidate.confidence <= 1:
        return "reject-invalid-confidence"
    if candidate.status in (MemoryStatus.QUARANTINED, MemoryStatus.RETIRED):
        return "reject-inactive"
    if candidate.status != MemoryStatus.VALIDATED:
        return "hold-validation"
    return "eligible-for-storage"

def retrieval_allowed(candidate: MemoryCandidate, requesting_user_id: str) -> bool:
    return (requesting_user_id == candidate.user_id
            and admission_decision(candidate) == "eligible-for-storage")
