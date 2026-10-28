import unittest
from sonny_one.apl.directedness import assess_target_repair


class DirectednessTests(unittest.TestCase):
    def test_target_repair_can_coexist_with_heldout_regression(self):
        result = assess_target_repair(
            {"target": False, "other": False, "passed": True},
            {"target": True, "other": False, "passed": True},
            target_task="target", heldout_parent={"new": True},
            heldout_candidate={"new": False})
        self.assertTrue(result["target_repaired"])
        self.assertEqual(result["target_minus_other_repair_rate"], 1)
        self.assertEqual(result["heldout"]["net_pass_delta"], -1)
        self.assertFalse(result["generalization_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_other_failures_can_repair_without_target(self):
        result = assess_target_repair(
            {"target": False, "other1": False, "other2": False, "passed": True},
            {"target": False, "other1": True, "other2": False, "passed": False},
            target_task="target")
        self.assertFalse(result["target_repaired"])
        self.assertEqual(result["other_failure_repair_rate"], .5)
        self.assertEqual(result["target_minus_other_repair_rate"], -.5)
        self.assertEqual(result["development_regressions"], 1)
        self.assertIsNone(result["heldout"])

    def test_rejects_nonfailed_target(self):
        with self.assertRaises(ValueError):
            assess_target_repair({"target": True, "other": False},
                                 {"target": True, "other": True}, target_task="target")

    def test_rejects_nonboolean_outcomes(self):
        with self.assertRaises(ValueError):
            assess_target_repair({"target": 0, "other": False},
                                 {"target": True, "other": True}, target_task="target")

    def test_rejects_missing_other_failure(self):
        with self.assertRaises(ValueError):
            assess_target_repair({"target": False, "passed": True},
                                 {"target": True, "passed": True}, target_task="target")

    def test_rejects_heldout_overlap(self):
        with self.assertRaises(ValueError):
            assess_target_repair({"target": False, "other": False},
                                 {"target": True, "other": True}, target_task="target",
                                 heldout_parent={"target": False}, heldout_candidate={"target": True})

    def test_rejects_incomplete_heldout(self):
        with self.assertRaises(ValueError):
            assess_target_repair({"target": False, "other": False},
                                 {"target": True, "other": True}, target_task="target",
                                 heldout_parent={"new": False})

    def test_rejects_mismatched_development_tasks(self):
        with self.assertRaises(ValueError):
            assess_target_repair({"target": False, "other": False},
                                 {"target": True}, target_task="target")


if __name__ == "__main__":
    unittest.main()
