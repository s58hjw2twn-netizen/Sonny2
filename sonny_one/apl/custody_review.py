"""Fail-closed review of APL execution evidence under independent custody.

Authenticity here means an envelope matches the configured custodian key.
It does not prove benchmark correctness, sandbox integrity, or independence.
No code is executed and no commit or promotion can be authorized.
"""
from .custody import verify_evidence


def review_custodied_apl_evidence(evaluation: dict, record: dict, envelope: dict,
                                 key: bytes, expected_custodian: str) -> dict:
    if not isinstance(evaluation, dict) or not isinstance(record, dict):
        raise ValueError("evaluation and record must be mappings")
    required = ("candidate_id", "base_revision", "trusted_suite_sha256",
                "heldout_suite_sha256", "image")
    if any(not isinstance(evaluation.get(k), str) or not evaluation[k] for k in required):
        raise ValueError("evaluation identity incomplete")
    if set(record) != set(required) | {"runner_status", "promotion"}:
        raise ValueError("unexpected custody record fields")
    if any(record[k] != evaluation[k] for k in required):
        raise ValueError("custody record does not match evaluation")
    if record["runner_status"] != evaluation.get("status"):
        raise ValueError("runner status mismatch")
    if record["promotion"] != "FORBIDDEN" or evaluation.get("promotion") != "FORBIDDEN":
        raise ValueError("promotion boundary mismatch")
    authentic = verify_evidence(record, envelope, key,
                                expected_custodian=expected_custodian)
    return {
        "candidate_id": evaluation["candidate_id"],
        "custody_envelope_valid": authentic,
        "runner_status": evaluation.get("status"),
        "independently_verified": False,
        "commit_allowed": False,
        "promotion_allowed": False,
        "status": "CUSTODY_CHECK_PASSED_REPLICATION_REQUIRED" if authentic
                  else "REJECTED_INVALID_CUSTODY",
    }
