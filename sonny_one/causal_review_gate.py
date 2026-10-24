"""Fail-closed bridge from locally recorded task results to self-model observations.

Receipts prove byte consistency only, not truth. A trusted reviewer must
authenticate the source and verdict outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from sonny_one.causal_evidence import EvidenceReceipt, verify_receipt
from sonny_one.causal_self_model import CausalSelfModel


@dataclass(frozen=True)
class ReviewedOutcome:
    task_id: str
    succeeded: bool
    reviewer_id: str
    receipt: EvidenceReceipt


def record_reviewed_outcome(
    model: CausalSelfModel,
    review: ReviewedOutcome,
    payload: bytes,
    *,
    trusted_reviewers: frozenset[str],
) -> None:
    if not isinstance(review, ReviewedOutcome):
        raise ValueError("review required")
    if type(review.succeeded) is not bool:
        raise ValueError("boolean verdict required")
    if not review.reviewer_id or review.reviewer_id not in trusted_reviewers:
        raise PermissionError("reviewer not trusted")
    if not verify_receipt(review.receipt, review.task_id, payload):
        raise ValueError("evidence digest or task mismatch")
    if review.receipt.authenticated:
        raise ValueError("caller-set authentication flag is not accepted")
    model.observe(review.task_id, review.succeeded, review.receipt.digest)
