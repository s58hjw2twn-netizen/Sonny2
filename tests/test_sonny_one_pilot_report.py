import unittest

from sonny_one.integration.pilot_evaluation import TaskEvidence
from sonny_one.integration.pilot_report import render_pilot_report


class PilotReportTests(unittest.TestCase):
    def test_empty_report_is_inconclusive(self):
        report = render_pilot_report([])
        self.assertIn("INSUFFICIENT EVIDENCE", report)
        self.assertIn("Not calculable", report)
        self.assertIn("Unknown or unverified:** 0", report)

    def test_report_distinguishes_verified_and_unknown(self):
        stamp = "2026-11-02T10:00:00+00:00"
        records = [
            TaskEvidence("synthetic-1", stamp, "research", "completed", "verified", "success"),
            TaskEvidence("synthetic-2", stamp, "calendar", "awaiting_input"),
        ]
        report = render_pilot_report(records)
        self.assertIn("Verified and scored:** 1", report)
        self.assertIn("Unknown or unverified:** 1", report)
        self.assertIn("100.0% (verified scored tasks only)", report)
        self.assertIn("NOT A PASS VERDICT", report)

    def test_rejects_multiline_label(self):
        with self.assertRaises(ValueError):
            render_pilot_report([], pilot_label="pilot\nInjected result")


if __name__ == "__main__":
    unittest.main()
