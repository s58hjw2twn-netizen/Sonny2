import unittest

from sonny_one.causal_self_model import CausalSelfModel


class CausalSelfModelTests(unittest.TestCase):
    def setUp(self):
        self.model = CausalSelfModel({"memory": True, "external_actions": False})

    def test_prediction_and_observation(self):
        self.model.predict("t1", "memory", 0.8, "prior test")
        self.model.observe("t1", True, "test-log-001")
        report = self.model.report()
        self.assertEqual(report["observed"], 1)
        self.assertAlmostEqual(report["brier_score"], 0.04)
        self.assertFalse(report["self_awareness_verified"])

    def test_no_unverified_success(self):
        self.model.predict("t1", "memory", 0.7, "test")
        report = self.model.report()
        self.assertEqual(report["unobserved"], 1)
        self.assertIsNone(report["brier_score"])

    def test_disabled_capability_fails_closed(self):
        with self.assertRaises(PermissionError):
            self.model.predict("t1", "external_actions", 1, "test")

    def test_invalid_confidence_rejected(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.model.predict("t1", "memory", value, "test")

    def test_unknown_observation_rejected(self):
        with self.assertRaises(ValueError):
            self.model.observe("missing", True, "proof")

    def test_duplicate_prediction_rejected(self):
        self.model.predict("t1", "memory", 0.5, "test")
        with self.assertRaises(ValueError):
            self.model.predict("t1", "memory", 0.5, "test")

    def test_no_evidence_rejected(self):
        self.model.predict("t1", "memory", 0.5, "test")
        with self.assertRaises(ValueError):
            self.model.observe("t1", True, "")


if __name__ == "__main__":
    unittest.main()
