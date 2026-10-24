import unittest
from unittest.mock import patch

from sonny_one.development_controller.development_agent import DevelopmentAgent
from sonny_one.development_controller.local_preflight_adapter import (
    LocalPreflightAdapter, run_local_preflight,
)


def queue():
    return {"version": 1, "tasks": [
        {"id": "DEV-101", "track": "app", "title": "Local preflight check",
         "state": "ready", "priority": 1, "requires_approval": False}
    ]}


class LocalPreflightAdapterTests(unittest.TestCase):
    def test_preflight_does_not_advance_agent(self):
        adapter = LocalPreflightAdapter()
        q = queue()
        with patch("sonny_one.development_controller.local_preflight_adapter.execute_validation",
                   return_value={"passed": True, "return_code": 0, "duration_seconds": 0.01}):
            result = DevelopmentAgent(adapter).run(q, authorized=True)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.tasks_completed, 0)
        self.assertEqual(q["tasks"][0]["state"], "ready")
        self.assertTrue(adapter.last_report["passed"])
        self.assertFalse(adapter.last_report["commit_created"])

    def test_rejects_unapproved_task(self):
        task = {**queue()["tasks"][0], "requires_approval": True}
        with self.assertRaises(PermissionError):
            run_local_preflight(task)

    def test_rejects_unknown_validation(self):
        with self.assertRaises(ValueError):
            LocalPreflightAdapter("arbitrary-shell-command")

    def test_no_validation_runs_without_authorization(self):
        adapter = LocalPreflightAdapter()
        q = queue()
        with patch("sonny_one.development_controller.local_preflight_adapter.execute_validation") as runner:
            result = DevelopmentAgent(adapter).run(q, authorized=False)
        self.assertEqual(result.status, "blocked")
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
