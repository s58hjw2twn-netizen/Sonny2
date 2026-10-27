import unittest

from sonny_one.apl.custody import seal_evidence
from sonny_one.apl.custody_review import review_custodied_apl_evidence, review_runner_report, review_anchored_runner_report, review_paired_replication

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
    with unittest.TestCase().assertRaisesRegex(ValueError, "does not match"):
        review_custodied_apl_evidence(
            EVALUATION, item, envelope, KEY, "independent-test")


def test_promotion_claim_rejected():
    item = record()
    item["promotion"] = "ALLOWED"
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    with unittest.TestCase().assertRaisesRegex(ValueError, "promotion boundary"):
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
    with unittest.TestCase().assertRaisesRegex(ValueError, "incomplete"):
        review_runner_report(report, {}, KEY, "independent-test")


def anchored_fixture(tmp, *, prefix=None):
    import json
    from pathlib import Path
    from sonny_one.apl.policy import append_lineage, sha256_bytes
    from sonny_one.apl.provenance import create_authenticated_anchor
    report = runner_report()
    ledger = Path(tmp) / "ledger.jsonl"
    if prefix is not None:
        append_lineage(ledger, {"replication_run": prefix})
    payload = dict(report)
    payload.pop("lineage_hash", None)
    entry = {k: report[k] for k in (
        "candidate_id", "base_revision", "image", "trusted_suite_sha256",
        "heldout_suite_sha256", "status")}
    entry["report_sha256"] = sha256_bytes(json.dumps(payload, sort_keys=True).encode())
    report["lineage_hash"] = append_lineage(ledger, entry)
    envelope = seal_evidence(runner_record(report), KEY, custodian_id="independent-test")
    anchor = create_authenticated_anchor(ledger, KEY, key_id="offline-test")
    return report, ledger, anchor, envelope


def test_anchored_report_valid_but_never_approves_commit():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        report, ledger, anchor, envelope = anchored_fixture(tmp)
        result = review_anchored_runner_report(report, ledger, anchor, KEY,
                                               envelope, KEY, "independent-test")
        assert result["ledger_anchor_valid"] is True
        assert result["custody_envelope_valid"] is True
        assert result["commit_allowed"] is False
        assert result["independently_verified"] is False


def test_anchored_report_rejects_ledger_rewrite():
    import tempfile
    from sonny_one.apl.policy import append_lineage
    with tempfile.TemporaryDirectory() as tmp:
        report, ledger, anchor, envelope = anchored_fixture(tmp)
        append_lineage(ledger, {"event": "tampered"})
        with unittest.TestCase().assertRaisesRegex(ValueError, "anchor authentication"):
            review_anchored_runner_report(report, ledger, anchor, KEY,
                                          envelope, KEY, "independent-test")


def test_anchored_report_rejects_wrong_anchor_key():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        report, ledger, anchor, envelope = anchored_fixture(tmp)
        with unittest.TestCase().assertRaisesRegex(ValueError, "anchor authentication"):
            review_anchored_runner_report(report, ledger, anchor, b"x" * 32,
                                          envelope, KEY, "independent-test")


def test_paired_replication_rejects_different_candidate_identity():
    first, second = runner_report(), runner_report()
    second["candidate_id"] = "f" * 64
    with unittest.TestCase().assertRaisesRegex(ValueError, "identity or fixtures"):
        review_paired_replication(first, None, {}, {}, second, None, {}, {},
                                  anchor_key=KEY, custody_key=KEY,
                                  expected_custodian="independent-test")


def test_paired_replication_rejects_reused_lineage():
    first, second = runner_report(), runner_report()
    with unittest.TestCase().assertRaisesRegex(ValueError, "distinct lineage"):
        review_paired_replication(first, None, {}, {}, second, None, {}, {},
                                  anchor_key=KEY, custody_key=KEY,
                                  expected_custodian="independent-test")


def test_paired_replication_rejects_missing_report():
    with unittest.TestCase().assertRaisesRegex(ValueError, "both runner reports"):
        review_paired_replication(None, None, {}, {}, {}, None, {}, {},
                                  anchor_key=KEY, custody_key=KEY,
                                  expected_custodian="independent-test")


def test_paired_replication_rejects_reused_ledger_path():
    first, second = runner_report(), runner_report()
    second["lineage_hash"] = "e" * 64
    with unittest.TestCase().assertRaisesRegex(ValueError, "distinct ledger paths"):
        review_paired_replication(first, "same-ledger", {}, {},
                                  second, "same-ledger", {}, {},
                                  anchor_key=KEY, custody_key=KEY,
                                  expected_custodian="independent-test")


def test_paired_custody_consistent_but_independence_not_proven():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "first").mkdir()
        Path(tmp, "second").mkdir()
        first, first_ledger, first_anchor, first_envelope = anchored_fixture(
            Path(tmp, "first"), prefix="first")
        second, second_ledger, second_anchor, second_envelope = anchored_fixture(
            Path(tmp, "second"), prefix="second")
        result = review_paired_replication(
            first, first_ledger, first_anchor, first_envelope,
            second, second_ledger, second_anchor, second_envelope,
            anchor_key=KEY, custody_key=KEY,
            expected_custodian="independent-test")
        assert result["paired_custody_valid"] is True
        assert result["independently_verified"] is False
        assert result["separate_execution_independently_established"] is False
        assert result["commit_allowed"] is False
