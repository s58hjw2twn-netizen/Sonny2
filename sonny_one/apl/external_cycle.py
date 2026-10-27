"""Fail-closed handoff from local candidate bytes to signed external review.

This interface is for a trusted controller. It does not execute external
holdouts or establish evaluator custody. No automatic promotion is possible.
"""
from .holdout_manifest import create_holdout_request, canonical_request_sha256
from .holdout_request import review_pinned_holdout_request


def prepare_external_evaluation(candidate_bytes, *, base_revision, suite_sha256):
    request = create_holdout_request(
        candidate_bytes, base_revision=base_revision, suite_sha256=suite_sha256)
    return {"request": request, "request_sha256": canonical_request_sha256(request)}


def review_external_evaluation(prepared, attestation, *,
                               trusted_evaluator_id,
                               trusted_public_key_pem,
                               trusted_public_key_sha256):
    if not isinstance(prepared, dict) or set(prepared) != {"request", "request_sha256"}:
        raise ValueError("Invalid prepared evaluation envelope")
    digest = canonical_request_sha256(prepared["request"])
    if not isinstance(prepared["request_sha256"], str) or digest != prepared["request_sha256"]:
        raise ValueError("Prepared request digest mismatch")
    result = review_pinned_holdout_request(
        prepared["request"], attestation,
        trusted_evaluator_id=trusted_evaluator_id,
        trusted_public_key_pem=trusted_public_key_pem,
        trusted_public_key_sha256=trusted_public_key_sha256)
    return {**result, "request_sha256": digest,
            "promotion": "FORBIDDEN", "improvement_proven": False}
