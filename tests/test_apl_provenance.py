"""Report/ledger binding regressions; no Docker execution required."""
import json
import tempfile
import unittest
from pathlib import Path
from sonny_one.apl.policy import append_lineage, sha256_bytes
from sonny_one.apl.provenance import verify_report_lineage


class ProvenanceTests(unittest.TestCase):
    def test_matching_report_and_lineage(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            report = {"candidate_id": "c", "base_revision": "r", "image": "i",
                      "trusted_suite_sha256": "t", "heldout_suite_sha256": "h",
                      "status": "REJECTED"}
            entry = dict(report, report_sha256=sha256_bytes(json.dumps(report, sort_keys=True).encode()))
            report["lineage_hash"] = append_lineage(ledger, entry)
            self.assertTrue(verify_report_lineage(report, ledger))
            altered = dict(report, status="ELIGIBLE_FOR_HUMAN_REVIEW")
            self.assertFalse(verify_report_lineage(altered, ledger))
            altered = dict(report, lineage_hash="0"*64)
            self.assertFalse(verify_report_lineage(altered, ledger))
            ledger.write_text(ledger.read_text().replace('"candidate_id": "c"', '"candidate_id": "x"'))
            self.assertFalse(verify_report_lineage(report, ledger))

    def test_missing_ledger_or_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "missing"
            self.assertFalse(verify_report_lineage({}, ledger))
            self.assertFalse(verify_report_lineage({"lineage_hash": "a"}, ledger))

    def test_independent_hmac_anchor_detects_rewrite_and_wrong_key(self):
        from sonny_one.apl.provenance import create_authenticated_anchor, verify_authenticated_anchor
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger"
            append_lineage(ledger, {"event": "first"})
            secret = b"k" * 32
            anchor = create_authenticated_anchor(ledger, secret, key_id="offline-custodian")
            self.assertTrue(verify_authenticated_anchor(ledger, anchor, secret))
            self.assertFalse(verify_authenticated_anchor(ledger, anchor, b"x" * 32))
            append_lineage(ledger, {"event": "next"})
            self.assertFalse(verify_authenticated_anchor(ledger, anchor, secret))
            with self.assertRaises(ValueError):
                create_authenticated_anchor(ledger, b"weak", key_id="offline")

    def test_anchor_rejects_invalid_metadata(self):
        from sonny_one.apl.provenance import create_authenticated_anchor, verify_authenticated_anchor
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger"
            append_lineage(ledger, {"event": "first"})
            anchor = create_authenticated_anchor(ledger, b"k" * 32, key_id="custodian")
            altered = dict(anchor, format="unknown")
            self.assertFalse(verify_authenticated_anchor(ledger, altered, b"k" * 32))
