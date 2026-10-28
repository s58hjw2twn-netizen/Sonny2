import tempfile
import unittest
from pathlib import Path
from sonny_vision.assurance import AssuranceError, Evidence, FailureLedger
from sonny_vision.reliability_gates import (
    ChangePlan, Source, acceptance_gate, compare_frozen_benchmark,
    fingerprint, recovery_decision, validate_change_plan, validate_sources)


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "original.bin"
        self.original.write_bytes(b"locked original")
        self.plan = ChangePlan(fingerprint(self.original), ("collar.png",),
                               ("face.png",), ("pixels", "orientation"))

    def test_only_authorized_changes(self):
        self.assertTrue(validate_change_plan(self.plan, ["collar.png"], self.original))

    def test_reject_unauthorized_changes(self):
        with self.assertRaises(AssuranceError):
            validate_change_plan(self.plan, ["face.png"], self.original)

    def test_reject_modified_original(self):
        self.original.write_bytes(b"changed")
        with self.assertRaises(AssuranceError):
            validate_change_plan(self.plan, ["collar.png"], self.original)

    def test_missing_provenance(self):
        result = validate_sources(["1987 uniform", "orientation"],
            [Source("manual", "USMC", "1987", "2026-10-28", ("1987 uniform",))])
        self.assertEqual(result["status"], "unverified")

    def test_full_provenance_mapping(self):
        result = validate_sources(["orientation"],
            [Source("manual", "USMC", "1987", "2026-10-28", ("orientation",))])
        self.assertEqual(result["status"], "documented")

    def test_acceptance_requires_approval(self):
        evidence = [Evidence("pixels", True, "pixel_checker", "audit:1"),
                    Evidence("orientation", True, "historian", "manual:1")]
        result = acceptance_gate(self.plan, evidence, creator="editor")
        self.assertEqual(result["status"], "awaiting_customer_approval")

    def test_acceptance_missing_evidence(self):
        result = acceptance_gate(self.plan,
            [Evidence("pixels", True, "pixel_checker", "audit:1")],
            creator="editor", customer_approved=True)
        self.assertEqual(result["status"], "unverified")

    def test_benchmark_rejects_regression(self):
        result = compare_frozen_benchmark({"a": 0.8, "b": 0.9},
                                          {"a": 0.9, "b": 0.8}, ["a", "b"])
        self.assertEqual(result["status"], "rejected")

    def test_benchmark_requires_actual_gain(self):
        result = compare_frozen_benchmark({"a": 0.8}, {"a": 0.8}, ["a"])
        self.assertEqual(result["status"], "rejected")

    def test_benchmark_accepts_nonregressing_gain(self):
        result = compare_frozen_benchmark({"a": 0.8, "b": 0.9},
                                          {"a": 0.9, "b": 0.9}, ["a", "b"])
        self.assertEqual(result["status"], "candidate_improved")

    def test_recovery_escalates_after_repeated_failures(self):
        ledger = FailureLedger(self.root / "failures.jsonl")
        for i in range(2):
            ledger.record(task_type="collar", method="generator",
                          failure_code="orientation", evidence_ref=str(i))
        self.assertEqual(recovery_decision("collar", ["generator"], ledger)["status"], "escalate")


if __name__ == "__main__":
    unittest.main()
