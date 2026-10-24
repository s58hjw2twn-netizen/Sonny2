import unittest
from sonny_one.development_controller.handoff import build_handoff
from sonny_one.development_controller.runner_gate import (
    runner_available, validate_execution_grant,
)


class RunnerGateTests(unittest.TestCase):
    def setUp(self):
        self.handoff = build_handoff({"version": 1, "tasks": [{
            "id": "APP-001", "track": "app", "title": "Local regression test",
            "state": "ready", "priority": 1, "requires_approval": False
        }]})
        self.grant = {
            "task_id": "APP-001", "branch": "research/apl-001",
            "sandbox_verified": True, "credential_scope_verified": True,
            "owner_policy_verified": True, "paid_services_enabled": False,
            "production_deploy_enabled": False, "merge_main_enabled": False
        }

    def test_review_is_not_execution(self):
        result = validate_execution_grant(self.handoff, self.grant)
        self.assertTrue(result["review_gate_passed"])
        self.assertFalse(result["execution_started"])
        self.assertFalse(result["grant_authenticity_verified"])
        self.assertFalse(runner_available())

    def test_rejects_mismatched_task(self):
        self.grant["task_id"] = "APP-002"
        with self.assertRaises(PermissionError):
            validate_execution_grant(self.handoff, self.grant)

    def test_rejects_unverified_sandbox(self):
        self.grant["sandbox_verified"] = False
        with self.assertRaises(PermissionError):
            validate_execution_grant(self.handoff, self.grant)

    def test_rejects_production_deployment(self):
        self.grant["production_deploy_enabled"] = True
        with self.assertRaises(PermissionError):
            validate_execution_grant(self.handoff, self.grant)

    def test_rejects_ungated_extra_field(self):
        self.grant["override"] = True
        with self.assertRaises(PermissionError):
            validate_execution_grant(self.handoff, self.grant)

    def test_rejects_missing_task(self):
        self.handoff["task"] = None
        with self.assertRaises(PermissionError):
            validate_execution_grant(self.handoff, self.grant)


if __name__ == "__main__":
    unittest.main()
