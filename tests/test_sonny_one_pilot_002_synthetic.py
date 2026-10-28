"""Synthetic-only Pilot 002 dry run. No personal data or external side effects."""
import unittest

from sonny_one.integration.pilot_evaluation import TaskEvidence, scorecard


class Pilot002SyntheticDryRun(unittest.TestCase):
    def test_mixed_outcomes_keep_unknowns_out_of_success_rate(self):
        stamp = "2026-11-02T10:00:00+00:00"
        records = [
            TaskEvidence("synthetic-001", stamp, "planning", "completed", "verified", "success", 0, True),
            TaskEvidence("synthetic-002", stamp, "research", "completed", "verified", "failure", 1, False),
            TaskEvidence("synthetic-003", stamp, "calendar", "awaiting_input", "unknown", "unknown"),
            TaskEvidence("synthetic-004", stamp, "shopping", "completed", "unverified", "unknown"),
            TaskEvidence("synthetic-005", stamp, "travel", "blocked", "unknown", "unknown"),
        ]
        report = scorecard(records)
        self.assertEqual(report["total_recorded"], 5)
        self.assertEqual(report["verified_scored"], 2)
        self.assertEqual(report["verified_successes"], 1)
        self.assertEqual(report["verified_failures"], 1)
        self.assertEqual(report["unknown_or_unverified"], 3)
        self.assertEqual(report["verified_success_rate"], 0.5)
        self.assertEqual(report["corrections_recorded"], 1)
        self.assertEqual(report["status_counts"]["completed"], 3)
        self.assertIn("only verified scored tasks", report["coverage_note"])


if __name__ == "__main__":
    unittest.main()
