"""Preflight remains fail-closed until a trusted runner exists."""
import unittest
from sonny_one.development_controller.runner_preflight import preflight

QUEUE = {"version": 1, "tasks": [{"id": "DEV-001", "track": "app", "title": "Test bounded task", "state": "ready", "priority": 1, "requires_approval": False}]}

class RunnerPreflightTests(unittest.TestCase):
    def test_static_repository_does_not_claim_runner_or_unattended_ready(self):
        result = preflight(QUEUE)
        self.assertFalse(result["runner_connected"])
        self.assertFalse(result["can_start_unattended"])
        self.assertIn("No independently authenticated", result["reason"])
        self.assertFalse(result["handoff"]["execution_authorized"])
        self.assertFalse(result["handoff"]["write_credentials_provided"])
        self.assertEqual(result["handoff"]["branch"], "research/apl-001")

    def test_preflight_keeps_production_effects_disabled(self):
        handoff = preflight(QUEUE)["handoff"]
        for key in ("paid_services_authorized", "merge_authorized", "deployment_authorized", "secret_access_authorized"):
            self.assertFalse(handoff[key])

if __name__ == "__main__":
    unittest.main()
