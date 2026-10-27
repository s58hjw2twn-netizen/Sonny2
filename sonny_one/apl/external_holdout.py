"""Fail-closed custody contract for future confidential holdout evaluation.

The existing APL Docker evaluator mounts tests inside the candidate container.
This module does not claim that those tests are confidential. It provides a
minimal evidence boundary for a future externally operated evaluator.
"""
import hashlib
import json
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def verify_external_holdout_attestation(attestation, *, candidate_sha256,
                                        base_revision, expected_evaluator):
    """Validate the shape and binding of an external result, not its authenticity.

    An independently controlled signature verifier and key custody are still
    required before results can count as trusted confidential evidence.
    """
    if not isinstance(attestation, dict) or set(attestation) != {
            "candidate_sha256", "base_revision", "evaluator_id",
            "suite_sha256", "result", "signature", "schema_version"}:
        raise ValueError("Invalid external attestation fields")
    if attestation["schema_version"] != 1:
        raise ValueError("Unsupported attestation schema")
    if not isinstance(candidate_sha256, str) or not _SHA.fullmatch(candidate_sha256):
        raise ValueError("Invalid expected candidate digest")
    if not isinstance(base_revision, str) or not _REV.fullmatch(base_revision):
        raise ValueError("Invalid expected revision")
    if not isinstance(expected_evaluator, str) or not expected_evaluator:
        raise ValueError("Missing evaluator identity")
    if attestation["candidate_sha256"] != candidate_sha256:
        raise ValueError("Candidate digest mismatch")
    if attestation["base_revision"] != base_revision:
        raise ValueError("Revision mismatch")
    if attestation["evaluator_id"] != expected_evaluator:
        raise ValueError("Evaluator identity mismatch")
    if not isinstance(attestation["suite_sha256"], str) or not _SHA.fullmatch(attestation["suite_sha256"]):
        raise ValueError("Invalid suite digest")
    if attestation["result"] not in ("PASS", "FAIL", "ERROR"):
        raise ValueError("Invalid holdout result")
    if not isinstance(attestation["signature"], str) or not attestation["signature"]:
        raise ValueError("Missing signature")
    canonical = {k: v for k, v in attestation.items() if k != "signature"}
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"attestation_sha256": digest, "candidate_sha256": candidate_sha256,
            "result_untrusted": attestation["result"],
            "signature_verified": False,
            "independent_custody_verified": False,
            "promotion": "FORBIDDEN", "improvement_proven": False}
