import unittest
from sonny_one.development_controller.runner_preflight import preflight


class RunnerPreflightTests(unittest.TestCase):
    def test_no_unattended_runner_claimed(self):
        result = preflight({"version": 1, "tasks": [{
            "id": "APP-001", "track": "app", "title": "Review local app",
            "state": "ready", "priority": 1, "requires_approval": False
        }]})
        self.assertFalse(result["runner_connected"])
        self.assertFalse(result["can_start_unattended"])
        self.assertFalse(result["handoff"]["execution_authorized"])
        self.assertEqual(len(result["next_setup_steps"]), 4)

    def test_empty_queue_still_fails_closed(self):
        result = preflight({"version": 1, "tasks": []})
        self.assertIsNone(result["handoff"]["task"])
        self.assertFalse(result["can_start_unattended"])


if __name__ == "__main__":
    unittest.main()
