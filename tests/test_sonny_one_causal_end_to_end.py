"""End-to-end synthetic custody -> APL validation -> paired holdout regression.

Fixtures are intentionally synthetic; this does not demonstrate real-world
improvement or independent scientific evaluation.
"""
import unittest

from sonny_one.apl.custody import seal_evidence
from sonny_one.causal_custody_bridge import custody_checked_apl_report
from sonny_one.causal_holdout import compare_holdout


def make_record(index, probability, eligible):
    candidate_id = "candidate-" + str(index)
    report = {"candidate_id": candidate_id,
              "status": "ELIGIBLE_FOR_HUMAN_REVIEW" if eligible else "REJECTED"}
    for suite in ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout"):
        report[suite] = {"exit_code": 0 if eligible else 1}
    return {"candidate_id": candidate_id, "predicted_pass": probability,
            "report": report}


class CausalEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.key = b"synthetic-test-custodian-key-000000000000"
        self.outcomes = [i % 2 == 0 for i in range(20)]
        self.candidate = [0.8 if outcome else 0.2 for outcome in self.outcomes]
        self.baseline = [0.5] * 20
        self.records = [make_record(i, self.candidate[i], outcome)
                        for i, outcome in enumerate(self.outcomes)]
        self.envelope = seal_evidence({"records": self.records}, self.key,
                                      custodian_id="fixture-custodian")

    def test_custody_to_holdout_pipeline(self):
        result = custody_checked_apl_report(
            self.records, self.envelope, custodian_key=self.key,
            custodian_id="fixture-custodian")
        self.assertTrue(result["custody_mac_verified"])
        self.assertEqual(result["self_model"]["observed"], 20)
        comparison = compare_holdout(self.baseline, self.candidate, self.outcomes)
        self.assertEqual(comparison["direction"], "candidate_better_descriptively")
        self.assertAlmostEqual(result["self_model"]["brier_score"],
                               comparison["candidate_brier"])
        self.assertFalse(result["independent_grading_verified"])
        self.assertFalse(comparison["statistical_significance_established"])

    def test_tampered_custody_stops_pipeline(self):
        self.records[0]["predicted_pass"] = 0.01
        with self.assertRaises(PermissionError):
            custody_checked_apl_report(
                self.records, self.envelope, custodian_key=self.key,
                custodian_id="fixture-custodian")


if __name__ == "__main__":
    unittest.main()
