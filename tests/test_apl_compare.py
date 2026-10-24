"""Offline tests for paired APL evaluation reports."""
import unittest
from sonny_one.apl.compare import compare


def report(deterministic, heldout, revision="a" * 40):
    return {"base_revision": revision,
            "deterministic": {"exit_code": deterministic},
            "heldout": {"exit_code": heldout}}


class TestPairedEvaluation(unittest.TestCase):
    def test_candidate_repair_is_not_proof(self):
        result = compare(report(1, 1), report(0, 0))
        self.assertTrue(result["suites"]["heldout"]["repair"])
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_regression_detected(self):
        result = compare(report(0, 0), report(0, 1))
        self.assertTrue(result["suites"]["heldout"]["regression"])

    def test_mismatched_revisions_rejected(self):
        with self.assertRaises(ValueError):
            compare(report(0, 0), report(0, 0, "b" * 40))

    def test_missing_heldout_rejected(self):
        with self.assertRaises(ValueError):
            compare(report(0, 0), {"base_revision": "a" * 40,
                                   "deterministic": {"exit_code": 0}})

    def test_boolean_exit_code_rejected(self):
        with self.assertRaises(ValueError):
            compare(report(0, 0), report(True, 0))


if __name__ == "__main__":
    unittest.main()
