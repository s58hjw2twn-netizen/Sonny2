"""Tests for read-only external grader evidence."""
import unittest
import json
import tempfile
import contextlib
import io
from unittest.mock import patch
from sonny_one.apl.evidence import main
from pathlib import Path
from sonny_one.apl.policy import append_lineage, sha256_bytes
from sonny_one.apl.evidence import attach_scores_verified
from sonny_one.apl.evidence import attach_scores


def identity():
    return {"candidate_id": "a" * 64, "base_revision": "b" * 40,
            "trusted_suite_sha256": "c" * 64,
            "heldout_suite_sha256": "d" * 64,
            "image": "runner@sha256:" + "e" * 64}


class TestExternalEvidence(unittest.TestCase):
    def test_scores_attach_without_changing_runner_decision(self):
        evaluation = dict(identity(), status="REJECTED", lineage_hash="f" * 64)
        evidence = dict(identity(), grader="independent-evaluator-1",
                        baseline_scores={"T1": 0, "T2": 1},
                        candidate_scores={"T1": 1, "T2": 1})
        result = attach_scores(evaluation, evidence)
        self.assertEqual(result["runner_status"], "REJECTED")
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["metrics"]["improved_tasks"], 1)
        self.assertEqual(evaluation["status"], "REJECTED")

    def test_verified_attachment_requires_intact_report_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "records.jsonl"
            evaluation = dict(identity(), status="REJECTED")
            digest = sha256_bytes(json.dumps(evaluation, sort_keys=True).encode())
            entry = dict(evaluation, report_sha256=digest)
            evaluation["lineage_hash"] = append_lineage(ledger, entry)
            evidence = dict(identity(), grader="external-grader",
                            baseline_scores={"T1": 0},
                            candidate_scores={"T1": 1})
            attached = attach_scores_verified(evaluation, evidence, ledger)
            self.assertTrue(attached["local_lineage_verified"])
            self.assertFalse(attached["improvement_proven"])
            altered = dict(evaluation, status="ELIGIBLE_FOR_HUMAN_REVIEW")
            with self.assertRaises(ValueError):
                attach_scores_verified(altered, evidence, ledger)
            with self.assertRaises(ValueError):
                attach_scores_verified(evaluation, evidence, Path(tmp)/"missing")

    def test_wrong_fixture_hash_rejected(self):
        evaluation = identity()
        evidence = dict(identity(), grader="grader", baseline_scores={"T1": 1},
                        candidate_scores={"T1": 1})
        evidence["heldout_suite_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            attach_scores(evaluation, evidence)

    def test_candidate_self_grading_rejected(self):
        evidence = dict(identity(), grader="candidate", baseline_scores={"T1": 1},
                        candidate_scores={"T1": 1})
        with self.assertRaises(ValueError):
            attach_scores(identity(), evidence)

    def test_missing_scores_rejected(self):
        evidence = dict(identity(), grader="grader")
        with self.assertRaises(ValueError):
            attach_scores(identity(), evidence)


    def test_cli_requires_ledger_and_rejects_unverified_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evaluation = dict(identity(), status="REJECTED", lineage_hash="0" * 64)
            evidence = dict(identity(), grader="external-grader",
                            baseline_scores={"T1": 0}, candidate_scores={"T1": 1})
            (root / "evaluation.json").write_text(json.dumps(evaluation))
            (root / "evidence.json").write_text(json.dumps(evidence))
            argv = ["apl-evidence", "--evaluation", str(root / "evaluation.json"),
                    "--evidence", str(root / "evidence.json")]
            with patch("sys.argv", argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main()
            with patch("sys.argv", argv + ["--ledger", str(root / "missing.jsonl")]):
                with self.assertRaises(ValueError):
                    main()


if __name__ == "__main__":
    unittest.main()
