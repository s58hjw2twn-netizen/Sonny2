import unittest
from sonny_one.product_readiness import ProductReadiness, current_verified_baseline


class ProductReadinessTests(unittest.TestCase):
    def test_current_baseline_is_not_production_ready(self):
        report = current_verified_baseline().report()
        self.assertFalse(report["production_ready"])
        self.assertEqual(len(report["missing_release_gates"]), 4)

    def test_research_does_not_enable_deployment(self):
        report = current_verified_baseline().report()
        self.assertFalse(report["automatic_deployment_allowed"])
        self.assertFalse(report["research_promotion_allowed"])

    def test_missing_security_review_blocks_release(self):
        flags = dict.fromkeys(ProductReadiness.__dataclass_fields__, True)
        flags["production_security_review_passed"] = False
        report = ProductReadiness(**flags).report()
        self.assertFalse(report["production_ready"])
        self.assertIn("production_security_review_passed",
                      report["missing_release_gates"])

    def test_all_gates_true_is_only_readiness_signal(self):
        flags = dict.fromkeys(ProductReadiness.__dataclass_fields__, True)
        report = ProductReadiness(**flags).report()
        self.assertTrue(report["production_ready"])
        self.assertFalse(report["automatic_deployment_allowed"])


if __name__ == "__main__":
    unittest.main()
