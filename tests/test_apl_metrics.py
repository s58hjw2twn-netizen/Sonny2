"""Tests for independent per-task metric evidence."""
import unittest
from sonny_one.apl.metrics import compare_metrics


class TestPairedMetrics(unittest.TestCase):
    def test_paired_score_summary(self):
        result = compare_metrics({"a": 0, "b": 1, "c": 0.5},
                                 {"a": 1, "b": 0, "c": 0.5})
        self.assertEqual(result["task_count"], 3)
        self.assertEqual(result["improved_tasks"], 1)
        self.assertEqual(result["regressed_tasks"], 1)
        self.assertEqual(result["unchanged_tasks"], 1)
        self.assertEqual(result["mean_delta"], 0)
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_missing_task_rejected(self):
        with self.assertRaises(ValueError):
            compare_metrics({"a": 1}, {"b": 1})

    def test_empty_reports_rejected(self):
        with self.assertRaises(ValueError):
            compare_metrics({}, {})

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            compare_metrics({"a": float("nan")}, {"a": 1})

    def test_bool_rejected(self):
        with self.assertRaises(ValueError):
            compare_metrics({"a": True}, {"a": 1})

    def test_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            compare_metrics({"a": 0}, {"a": 1.1})


if __name__ == "__main__":
    unittest.main()
