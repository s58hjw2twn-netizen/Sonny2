import unittest
from sonny_one.development_controller.handoff import build_handoff


class AgentHandoffTests(unittest.TestCase):
    def test_handoff_is_non_authorizing(self):
        queue = {"version": 1, "tasks": [{
            "id": "APP-001", "track": "app", "title": "Test code",
            "state": "ready", "priority": 1, "requires_approval": False
        }]}
        handoff = build_handoff(queue)
        self.assertEqual(handoff["task"]["id"], "APP-001")
        self.assertEqual(handoff["mode"], "proposal_only")
        for key in ("execution_authorized", "write_credentials_provided",
                    "network_access_authorized", "paid_services_authorized",
                    "merge_authorized", "deployment_authorized",
                    "secret_access_authorized",
                    "frozen_research_mutation_authorized"):
            self.assertFalse(handoff[key], key)

    def test_approval_required_task_is_not_handed_to_runner(self):
        queue = {"version": 1, "tasks": [{
            "id": "APP-003", "track": "app", "title": "Deploy production",
            "state": "ready", "priority": 1, "requires_approval": True
        }]}
        handoff = build_handoff(queue)
        self.assertIsNone(handoff["task"])
        self.assertEqual(handoff["owner_approval_required"], ["APP-003"])


if __name__ == "__main__":
    unittest.main()
