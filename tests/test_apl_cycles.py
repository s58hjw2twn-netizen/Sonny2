import unittest
from sonny_one.apl.metrics import compare_metrics
from sonny_one.apl.cycles import assess_cycles


def cycle(i, *, positive=True):
    baseline = {f"t{j}": 0.0 for j in range(20)}
    candidate = {f"t{j}": 1.0 if positive else 0.0 for j in range(20)}
    evaluation = {"status": "ELIGIBLE_FOR_HUMAN_REVIEW",
                  "candidate_id": f"candidate-{i}", "base_revision": "base",
                  "lineage_hash": f"lineage-{i}"}
    attachment = {"local_lineage_verified": True, "runner_status": evaluation["status"],
                  "candidate_id": evaluation["candidate_id"],
                  "base_revision": "base", "lineage_hash": evaluation["lineage_hash"],
                  "promotion": "FORBIDDEN", "improvement_proven": False,
                  "grader": "external-grader",
                  "metrics": compare_metrics(baseline, candidate)}
    return {"cycle_id": f"cycle-{i}", "suite_fingerprint": f"{i:064x}",
            "evaluation": evaluation, "attachment": attachment,
            "baseline_scores": baseline, "candidate_scores": candidate}


class CycleTests(unittest.TestCase):
    def test_repeated_positive_is_only_review(self):
        result = assess_cycles([cycle(1), cycle(2), cycle(3)], resamples=200)
        self.assertTrue(result["human_review_recommended"])
        self.assertFalse(result["recursive_improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_one_nonpositive_cycle_prevents_review(self):
        result = assess_cycles([cycle(1), cycle(2, positive=False), cycle(3)],
                               resamples=200)
        self.assertFalse(result["human_review_recommended"])

    def test_duplicate_suite_rejected(self):
        cycles = [cycle(1), cycle(2), cycle(3)]
        cycles[2]["suite_fingerprint"] = cycles[0]["suite_fingerprint"]
        with self.assertRaises(ValueError):
            assess_cycles(cycles, resamples=200)

    def test_duplicate_candidate_rejected(self):
        cycles = [cycle(1), cycle(2), cycle(3)]
        cycles[2]["evaluation"]["candidate_id"] = cycles[0]["evaluation"]["candidate_id"]
        with self.assertRaises(ValueError):
            assess_cycles(cycles, resamples=200)

    def test_missing_lineage_rejected(self):
        cycles = [cycle(1), cycle(2), cycle(3)]
        cycles[1]["attachment"]["local_lineage_verified"] = False
        with self.assertRaises(ValueError):
            assess_cycles(cycles, resamples=200)

    def test_insufficient_cycles_rejected(self):
        with self.assertRaises(ValueError):
            assess_cycles([cycle(1)], resamples=200)
