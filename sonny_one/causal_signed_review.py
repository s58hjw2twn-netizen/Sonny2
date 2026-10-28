"""Authenticated review envelopes for causal self-model outcomes.

HMAC authenticates a configured reviewer key, not the factual correctness of
the verdict. Keys must be provisioned outside source control. Replay protection
requires a durable consumed-nonce store in a production integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest, new
import json


@dataclass(frozen=True)
class SignedReview:
    task_id: str
    evidence_digest: str
    succeeded: bool
    reviewer_id: str
    nonce: str
    signature: str


def _message(task_id: str, digest: str, succeeded: bool, reviewer: str, nonce: str) -> bytes:
    return json.dumps([task_id, digest, succeeded, reviewer, nonce],
                      separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_review(task_id: str, evidence_digest: str, succeeded: bool,
                reviewer_id: str, nonce: str, *, key: bytes) -> SignedReview:
    if not all(isinstance(x, str) and x.strip()
               for x in (task_id, evidence_digest, reviewer_id, nonce)):
        raise ValueError("nonempty review fields required")
    if type(succeeded) is not bool or not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("boolean verdict and 32-byte minimum secret required")
    signature = new(key, _message(task_id, evidence_digest, succeeded,
                                  reviewer_id, nonce), sha256).hexdigest()
    return SignedReview(task_id, evidence_digest, succeeded, reviewer_id, nonce,
                        signature)


def verify_signed_review(review: SignedReview, *, reviewer_keys: dict[str, bytes],
                         consumed_nonces: set[tuple[str, str]]) -> bool:
    if not isinstance(review, SignedReview):
        return False
    key = reviewer_keys.get(review.reviewer_id)
    if not isinstance(key, bytes) or len(key) < 32:
        return False
    if (review.reviewer_id, review.nonce) in consumed_nonces:
        return False
    if type(review.succeeded) is not bool:
        return False
    expected = new(key, _message(review.task_id, review.evidence_digest,
                                 review.succeeded, review.reviewer_id,
                                 review.nonce), sha256).hexdigest()
    return compare_digest(expected, review.signature)


def record_signed_review(model, receipt, payload: bytes, review: SignedReview, *,
                         reviewer_keys: dict[str, bytes],
                         consumed_nonces: set[tuple[str, str]]) -> None:
    """Verify before recording; consume nonce only after successful observation.

    Caller owns the nonce store and must make observation+nonce writes atomic
    and persistent for production. This research adapter is single-process only.
    """
    from sonny_one.causal_evidence import verify_receipt
    if not verify_receipt(receipt, review.task_id, payload):
        raise ValueError("receipt does not match task payload")
    if receipt.digest != review.evidence_digest:
        raise ValueError("review not bound to receipt")
    if not verify_signed_review(review, reviewer_keys=reviewer_keys,
                                consumed_nonces=consumed_nonces):
        raise PermissionError("invalid or replayed reviewer signature")
    model.observe(review.task_id, review.succeeded, receipt.digest)
    consumed_nonces.add((review.reviewer_id, review.nonce))
