import tempfile
import unittest
from pathlib import Path
from sonny_vision.assurance import (AssuranceError, Constraint, Evidence,
                                    FailureLedger, choose_method, evaluate)


class AssuranceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = FailureLedger(Path(self.tmp.name) / "failures.jsonl")
        self.constraints = [Constraint("pixels"), Constraint("orientation")]

    def test_missing_check_fails_closed(self):
        d = evaluate(self.constraints, [Evidence("pixels", True, "pixel_validator", "audit:1")], creator="compositor")
        self.assertEqual(d.status, "unverified")
        self.assertEqual(d.missing, ["orientation"])

    def test_failed_check_rejects(self):
        d = evaluate(self.constraints, [Evidence("pixels", False, "pixel_validator", "audit:1"),
                                        Evidence("orientation", True, "human_reviewer", "ref:1987")], creator="compositor")
        self.assertEqual(d.status, "rejected")

    def test_independent_checks_verify(self):
        d = evaluate(self.constraints, [Evidence("pixels", True, "pixel_validator", "audit:1"),
                                        Evidence("orientation", True, "human_reviewer", "ref:1987")], creator="compositor")
        self.assertEqual(d.status, "verified")

    def test_self_verification_rejected(self):
        with self.assertRaises(AssuranceError):
            evaluate(self.constraints, [Evidence("pixels", True, "compositor", "audit:1")], creator="compositor")

    def test_method_switch_after_two_failures(self):
        for i in range(2):
            self.ledger.record(task_type="collar", method="whole_image_generation",
                               failure_code="changed_face", evidence_ref=f"audit:{i}")
        self.assertEqual(choose_method("collar", ["whole_image_generation", "masked_compositor"], self.ledger),
                         "masked_compositor")

    def test_tampered_ledger_detected(self):
        self.ledger.record(task_type="collar", method="generator",
                           failure_code="bad_orientation", evidence_ref="audit:1")
        p = self.ledger.path
        p.write_text(p.read_text().replace("bad_orientation", "success"))
        with self.assertRaises(AssuranceError):
            self.ledger.read()

    def test_no_methods_escalates(self):
        self.ledger.record(task_type="collar", method="generator",
                           failure_code="bad_orientation", evidence_ref="audit:1")
        with self.assertRaises(AssuranceError):
            choose_method("collar", ["generator"], self.ledger)


if __name__ == "__main__":
    unittest.main()
