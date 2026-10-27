import pytest

from sonny_one.apl.custody import seal_evidence
from sonny_one.apl.custody_review import review_custodied_apl_evidence, review_runner_report

KEY = b"local-test-only-independent-custodian-key-32bytes"
EVALUATION = {
    "candidate_id": "a" * 64,
    "base_revision": "b" * 40,
    "trusted_suite_sha256": "c" * 64,
    "heldout_suite_sha256": "d" * 64,
    "image": "test@sha256:" + "e" * 64,
    "status": "ELIGIBLE_FOR_REVIEW",
    "promotion": "FORBIDDEN",
}


def record():
    return {
        **{k: EVALUATION[k] for k in (
            "candidate_id", "base_revision", "trusted_suite_sha256",
            "heldout_suite_sha256", "image")},
        "runner_status": EVALUATION["status"],
        "promotion": "FORBIDDEN",
    }


def test_valid_custody_still_requires_replication():
    item = record()
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    result = review_custodied_apl_evidence(
        EVALUATION, item, envelope, KEY, "independent-test")
    assert result["custody_envelope_valid"] is True
    assert result["independently_verified"] is False
    assert result["commit_allowed"] is False
    assert result["promotion_allowed"] is False


def test_wrong_custodian_fails_closed():
    item = record()
    envelope = seal_evidence(item, KEY, custodian_id="wrong")
    result = review_custodied_apl_evidence(
        EVALUATION, item, envelope, KEY, "independent-test")
    assert result["custody_envelope_valid"] is False


def test_tampered_identity_rejected_even_if_resigned():
    item = record()
    item["candidate_id"] = "f" * 64
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    with pytest.raises(ValueError, match="does not match"):
        review_custodied_apl_evidence(
            EVALUATION, item, envelope, KEY, "independent-test")


def test_promotion_claim_rejected():
    item = record()
    item["promotion"] = "ALLOWED"
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    with pytest.raises(ValueError, match="promotion boundary"):
        review_custodied_apl_evidence(
            EVALUATION, item, envelope, KEY, "independent-test")


def runner_report():
    report = dict(EVALUATION, status="ELIGIBLE_FOR_HUMAN_REVIEW", lineage_hash="f" * 64)
    for field in ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout"):
        report[field] = {"exit_code": 0, "stdout_tail": "ok"}
    return report


def runner_record(report):
    fields = ("candidate_id", "base_revision", "trusted_suite_sha256",
              "heldout_suite_sha256", "image")
    record = {k: report[k] for k in fields}
    record.update(runner_status=report["status"], promotion="FORBIDDEN",
                  lineage_hash=report["lineage_hash"],
                  execution={k: report[k] for k in (
                      "baseline_deterministic", "baseline_heldout", "deterministic", "heldout")})
    return record


def test_custodied_runner_report_still_requires_replication():
    report = runner_report()
    envelope = seal_evidence(runner_record(report), KEY, custodian_id="independent-test")
    result = review_runner_report(report, envelope, KEY, "independent-test")
    assert result["custody_envelope_valid"] is True
    assert result["independently_verified"] is False
    assert result["commit_allowed"] is False


def test_runner_result_tampering_breaks_custody():
    report = runner_report()
    envelope = seal_evidence(runner_record(report), KEY, custodian_id="independent-test")
    report["heldout"]["stdout_tail"] = "changed"
    assert review_runner_report(report, envelope, KEY, "independent-test")["custody_envelope_valid"] is False


def test_runner_missing_heldout_result_fails_closed():
    report = runner_report()
    del report["heldout"]
    with pytest.raises(ValueError, match="incomplete"):
        review_runner_report(report, {}, KEY, "independent-test")
