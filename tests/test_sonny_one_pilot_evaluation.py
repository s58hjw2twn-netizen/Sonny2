import unittest

from sonny_one.integration.pilot_evaluation import TaskEvidence, scorecard


def task(task_id="t1", **kwargs):
    fields = dict(task_id=task_id, occurred_at="2026-11-01T09:00:00-04:00", category="planning", status="completed", verification="verified", outcome="success")
    fields.update(kwargs)
    return TaskEvidence(**fields)


class PilotEvaluationTests(unittest.TestCase):
    def test_empty_evidence_is_not_a_pass(self):
        result = scorecard([])
        self.assertIsNone(result["verified_success_rate"])
        self.assertEqual(result["verified_scored"], 0)

    def test_unknown_tasks_not_counted_as_successes_or_failures(self):
        result = scorecard([task(), task("t2", status="awaiting_input", verification="unknown", outcome="unknown")])
        self.assertEqual(result["verified_success_rate"], 1.0)
        self.assertEqual(result["unknown_or_unverified"], 1)
        self.assertEqual(result["verified_scored"], 1)

    def test_verified_failure_is_counted(self):
        result = scorecard([task(), task("t2", outcome="failure")])
        self.assertEqual(result["verified_success_rate"], 0.5)
        self.assertEqual(result["verified_failures"], 1)

    def test_unverified_success_is_rejected(self):
        with self.assertRaises(ValueError):
            task(verification="unverified", outcome="success")

    def test_incomplete_success_is_rejected(self):
        with self.assertRaises(ValueError):
            task(status="in_progress", outcome="success")

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            scorecard([task(), task()])

    def test_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            task(occurred_at="2026-11-01T09:00:00")

    def test_negative_corrections_rejected(self):
        with self.assertRaises(ValueError):
            task(correction_count=-1)


if __name__ == "__main__":
    unittest.main()
