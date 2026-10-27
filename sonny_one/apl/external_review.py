"""Review-only evidence intake for externally signed APL holdout results.

The caller must obtain its evaluator key and fingerprint from independent
trusted configuration, never from candidate code or the attestation itself.
This cannot establish actual independent custody or confidential execution.
"""
from .evaluator_trust import verify_with_pinned_evaluator


def review_external_holdout(attestation, *, candidate_sha256, base_revision,
                            trusted_evaluator_id, trusted_public_key_pem,
                            trusted_public_key_sha256):
    result = verify_with_pinned_evaluator(
        attestation, candidate_sha256=candidate_sha256,
        base_revision=base_revision,
        trusted_evaluator_id=trusted_evaluator_id,
        trusted_public_key_pem=trusted_public_key_pem,
        trusted_public_key_sha256=trusted_public_key_sha256)
    return {
        "candidate_sha256": candidate_sha256,
        "base_revision": base_revision,
        "evaluator_id": trusted_evaluator_id,
        "attestation_sha256": result["attestation_sha256"],
        "signature_verified": result["signature_verified"],
        "evaluator_key_pin_verified": result["evaluator_key_pin_verified"],
        "reported_holdout_result": result["result_untrusted"],
        "independent_custody_verified": False,
        "confidential_execution_verified": False,
        "promotion": "FORBIDDEN",
        "improvement_proven": False,
    }
