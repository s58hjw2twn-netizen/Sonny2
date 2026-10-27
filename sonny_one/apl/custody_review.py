"""Fail-closed review of APL execution evidence under independent custody.

Authenticity here means an envelope matches the configured custodian key.
It does not prove benchmark correctness, sandbox integrity, or independence.
No code is executed and no commit or promotion can be authorized.
"""
from .custody import verify_evidence
from .provenance import verify_report_lineage


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


def review_runner_report(evaluation: dict, envelope: dict, key: bytes,
                         expected_custodian: str) -> dict:
    """Bind the custody envelope to an actual APL report's execution fields.

    The caller must obtain the report from a trusted runner and keep the key
    outside the candidate environment. A valid MAC alone proves neither fact.
    """
    if not isinstance(evaluation, dict):
        raise ValueError("evaluation must be a mapping")
    fields = ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout")
    required = ("candidate_id", "base_revision", "trusted_suite_sha256",
                "heldout_suite_sha256", "image")
    if any(not isinstance(evaluation.get(k), str) or not evaluation[k] for k in required):
        raise ValueError("evaluation identity incomplete")
    if evaluation.get("promotion") != "FORBIDDEN":
        raise ValueError("promotion boundary mismatch")
    if evaluation.get("status") != "ELIGIBLE_FOR_HUMAN_REVIEW":
        raise ValueError("runner did not qualify for human review")
    if any(not isinstance(evaluation.get(k), dict)
           or type(evaluation[k].get("exit_code")) is not int
           or evaluation[k]["exit_code"] != 0 for k in fields):
        raise ValueError("paired execution results incomplete or failed")
    if not isinstance(evaluation.get("lineage_hash"), str) or len(evaluation["lineage_hash"]) != 64:
        raise ValueError("lineage hash missing")
    record = {k: evaluation[k] for k in required}
    record.update(runner_status=evaluation["status"], promotion="FORBIDDEN",
                  lineage_hash=evaluation["lineage_hash"],
                  execution={k: evaluation[k] for k in fields})
    authentic = verify_evidence(record, envelope, key,
                                expected_custodian=expected_custodian)
    return {
        "candidate_id": evaluation["candidate_id"],
        "custody_envelope_valid": authentic,
        "execution_records_present": True,
        "independently_verified": False,
        "commit_allowed": False,
        "promotion_allowed": False,
        "status": "CUSTODY_CHECK_PASSED_REPLICATION_REQUIRED" if authentic
                  else "REJECTED_INVALID_CUSTODY",
    }


def review_anchored_runner_report(evaluation: dict, ledger, anchor: dict,
                                  anchor_key: bytes, envelope: dict,
                                  custody_key: bytes, expected_custodian: str) -> dict:
    """Require a matching local ledger and independently keyed anchor.

    The caller must control the custody keys outside the experimental host.
    This still does not establish independent replication or approve commits.
    """
    from .provenance import verify_authenticated_anchor
    if not verify_report_lineage(evaluation, ledger):
        raise ValueError("runner report does not match valid local lineage")
    if not verify_authenticated_anchor(ledger, anchor, anchor_key):
        raise ValueError("ledger anchor authentication failed")
    result = review_runner_report(evaluation, envelope, custody_key,
                                  expected_custodian)
    result["ledger_anchor_valid"] = True
    result["status"] = ("ANCHORED_CUSTODY_VALID_REPLICATION_REQUIRED"
                        if result["custody_envelope_valid"]
                        else "REJECTED_INVALID_CUSTODY")
    return result


def review_paired_replication(primary: dict, primary_ledger, primary_anchor: dict,
                              primary_envelope: dict, replica: dict, replica_ledger,
                              replica_anchor: dict, replica_envelope: dict,
                              *, anchor_key: bytes, custody_key: bytes,
                              expected_custodian: str) -> dict:
    """Compare two separately supplied, anchored runner reports without promotion.

    The caller must independently establish that runs and custodians are separate.
    Identical self-reported data cannot establish independent replication.
    """
    keys = ("candidate_id", "base_revision", "image",
            "trusted_suite_sha256", "heldout_suite_sha256")
    if not isinstance(primary, dict) or not isinstance(replica, dict):
        raise ValueError("both runner reports required")
    if any(primary.get(k) != replica.get(k) for k in keys):
        raise ValueError("replication identity or fixtures differ")
    if primary.get("lineage_hash") == replica.get("lineage_hash"):
        raise ValueError("replication must have a distinct lineage record")
    from pathlib import Path
    try:
        if Path(primary_ledger).resolve() == Path(replica_ledger).resolve():
            raise ValueError("replication must use distinct ledger paths")
    except (TypeError, OSError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc) == "replication must use distinct ledger paths":
            raise
        raise ValueError("valid distinct ledger paths required") from exc
    first = review_anchored_runner_report(
        primary, primary_ledger, primary_anchor, anchor_key,
        primary_envelope, custody_key, expected_custodian)
    second = review_anchored_runner_report(
        replica, replica_ledger, replica_anchor, anchor_key,
        replica_envelope, custody_key, expected_custodian)
    authenticated = (first["custody_envelope_valid"] is True
                     and second["custody_envelope_valid"] is True)
    return {
        "candidate_id": primary["candidate_id"],
        "paired_custody_valid": authenticated,
        "separate_execution_independently_established": False,
        "independently_verified": False,
        "commit_allowed": False,
        "promotion_allowed": False,
        "status": ("PAIRED_CUSTODY_VALID_INDEPENDENCE_UNVERIFIED"
                   if authenticated else "REJECTED_INVALID_PAIRED_CUSTODY"),
    }
