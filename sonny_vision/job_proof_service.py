"""Trusted adapter for reading proof state before serving watermarked bytes."""
from __future__ import annotations
from .job_store import get_customer_job
from .proof_delivery import ProofResponse, serve_approval_proof


def serve_customer_job_proof(*, database_path: str, proof_path: str,
                             job_id: str, authenticated_customer_id: str,
                             token: str, secret: bytes, now: int) -> ProofResponse:
    record = get_customer_job(database_path, job_id, authenticated_customer_id)
    if record is None:
        return ProofResponse(403, b"Forbidden", {
            "Cache-Control": "no-store, private",
            "X-Content-Type-Options": "nosniff"})
    status, proof_sha256 = record
    return serve_approval_proof(
        proof_path=proof_path, job_id=job_id,
        customer_id=authenticated_customer_id,
        authenticated_customer_id=authenticated_customer_id,
        token=token, expected_proof_sha256=proof_sha256,
        secret=secret, now=now, proof_status=status)
