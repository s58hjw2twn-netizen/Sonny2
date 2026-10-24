"""Tests for read-only external grader evidence."""
import unittest
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


if __name__ == "__main__":
    unittest.main()
