import unittest
from sonny.rsi_evidence_gate import assess_experiment


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {"benchmark_id": "frozen-demo", "cases": ["a", "b"], "minimum_gain": 0.1, "maximum_regressions": 0, "fixture_sha256": "a" * 64}
        self.baseline = {"a": 0.5, "b": 0.5}

    def test_candidate_requires_independent_replication(self):
        result = assess_experiment(self.manifest, self.baseline, {"a": 0.7, "b": 0.7})
        self.assertTrue(result["meets_preregistered_thresholds"])
        self.assertFalse(result["independently_verified"])
        self.assertFalse(result["commit_allowed"])
        self.assertFalse(result["promotion_allowed"])

    def test_regression_rejected(self):
        result = assess_experiment(self.manifest, self.baseline, {"a": 0.4, "b": 1.0})
        self.assertFalse(result["meets_preregistered_thresholds"])

    def test_mismatched_cases_rejected(self):
        with self.assertRaises(ValueError):
            assess_experiment(self.manifest, self.baseline, {"a": 1.0, "other": 1.0})

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            assess_experiment(self.manifest, self.baseline, {"a": float("nan"), "b": 0.8})

    def test_zero_gain_rejected(self):
        with self.assertRaises(ValueError):
            assess_experiment(self.manifest, self.baseline, self.baseline)

    def test_invalid_manifest_rejected(self):
        self.manifest["maximum_regressions"] = True
        with self.assertRaises(ValueError):
            assess_experiment(self.manifest, self.baseline, {"a": 0.8, "b": 0.8})


if __name__ == "__main__":
    unittest.main()
