"""Approval-preview workflow: previews only; no clean-master release.

This module never returns the master bytes. Approval is an explicit customer
action stored by the calling application, not inferred from viewing the proof.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .approval_proof import write_approval_proof


@dataclass(frozen=True)
class ProofRecord:
    job_id: str
    proof_path: str
    status: str = "awaiting_customer_approval"


def prepare_customer_proof(job_id: str, master_path: str, proof_path: str) -> ProofRecord:
    if not job_id or not job_id.strip():
        raise ValueError("Job ID required")
    write_approval_proof(master_path, proof_path)
    return ProofRecord(job_id=job_id, proof_path=str(Path(proof_path)))


def customer_approval_status(record: ProofRecord, customer_approved: bool) -> str:
    """Approval alone never releases clean master or asserts payment received."""
    if record.status != "awaiting_customer_approval":
        raise ValueError("Invalid proof state")
    return "approved_pending_release_checks" if customer_approved else "revision_requested"
