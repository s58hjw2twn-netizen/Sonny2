"""Local evidence binding for Causal Self-Model observations.

SHA-256 binds a task result to exact bytes, but is not proof that the result is
truthful or independently verified. Caller must independently authenticate source.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest


@dataclass(frozen=True)
class EvidenceReceipt:
    task_id: str
    source: str
    digest: str
    authenticated: bool = False


def make_receipt(task_id: str, source: str, payload: bytes) -> EvidenceReceipt:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("task id required")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source required")
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("nonempty bytes required")
    return EvidenceReceipt(task_id, source, sha256(payload).hexdigest())


def verify_receipt(receipt: EvidenceReceipt, task_id: str, payload: bytes) -> bool:
    if not isinstance(receipt, EvidenceReceipt) or not isinstance(payload, bytes):
        return False
    return (receipt.task_id == task_id and
            compare_digest(receipt.digest, sha256(payload).hexdigest()))
