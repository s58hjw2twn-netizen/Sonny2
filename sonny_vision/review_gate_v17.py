"""V17 signed review gate: separate candidate acceptance from customer release.

Signatures bind a reviewed source and output digest, purpose, and reviewer's
explicit decision. Keys must come from an operator-managed secret store.
This is not face recognition or a substitute for independent image review.
"""
from __future__ import annotations
import hashlib
import hmac
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewDecision:
    source_sha256: str
    output_sha256: str
    reviewer: str
    purpose: str
    approved: bool
    signature: str


def _digest(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _payload(source: str, output: str, reviewer: str, purpose: str, approved: bool) -> bytes:
    if not _digest(source) or not _digest(output):
        raise ValueError("Expected lowercase SHA-256 digests")
    if not reviewer.strip() or purpose not in {"candidate_review", "customer_release"}:
        raise ValueError("Invalid reviewer or review purpose")
    return json.dumps({"approved": approved, "output": output, "purpose": purpose,
                       "reviewer": reviewer, "source": source},
                      sort_keys=True, separators=(",", ":")).encode()


def sign_decision(source: str, output: str, reviewer: str, purpose: str,
                  approved: bool, secret: bytes) -> ReviewDecision:
    if len(secret) < 32:
        raise ValueError("Review signing key must be at least 32 bytes")
    message = _payload(source, output, reviewer, purpose, approved)
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return ReviewDecision(source, output, reviewer, purpose, approved, signature)


def verify_decision(decision: ReviewDecision, source: str, output: str,
                    purpose: str, secret: bytes) -> bool:
    if len(secret) < 32 or not decision.approved or decision.purpose != purpose:
        return False
    if decision.source_sha256 != source or decision.output_sha256 != output:
        return False
    try:
        message = _payload(source, output, decision.reviewer, purpose, decision.approved)
    except ValueError:
        return False
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, decision.signature)


def authorize_customer_release(decision: ReviewDecision | None, source: bytes,
                               candidate: bytes, secret: bytes,
                               quality_passed: bool, identity_reviewed: bool) -> bool:
    """Default deny. Require a distinct signed release decision plus human checks."""
    if decision is None or not quality_passed or not identity_reviewed:
        return False
    return verify_decision(decision, hashlib.sha256(source).hexdigest(),
                           hashlib.sha256(candidate).hexdigest(),
                           "customer_release", secret)
