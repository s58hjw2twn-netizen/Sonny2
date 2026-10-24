import unittest
from unittest.mock import patch

from sonny_one.development_controller.development_agent import DevelopmentAgent
from sonny_one.development_controller.model_proposal_adapter import (
    ModelProposalAdapter, validate_model_proposal,
)


def task(task_id="RES-001"):
    return {"id": task_id, "track": "research", "title": "Research proposal",
            "state": "ready", "priority": 1, "requires_approval": False}


def proposal():
    return {"task_id": "RES-001", "patch_text": "diff --git a/sonny_one/apl_targets/offline_strategy.py b/sonny_one/apl_targets/offline_strategy.py\n--- a/sonny_one/apl_targets/offline_strategy.py\n+++ b/sonny_one/apl_targets/offline_strategy.py\n@@ -1 +1 @@\n-old\n+new\n"}


class ModelProposalAdapterTests(unittest.TestCase):
    def test_valid_proposal_remains_review_only(self):
        with patch("sonny_one.development_controller.model_proposal_adapter.validate_patch", return_value=["sonny_one/apl_targets/offline_strategy.py"]):
            result = validate_model_proposal(task(), proposal())
        self.assertTrue(result["review_only"])
        self.assertFalse(result["committed"])
        self.assertEqual(len(result["candidate_id"]), 64)

    def test_rejects_other_experimental_path(self):
        with patch("sonny_one.development_controller.model_proposal_adapter.validate_patch",
                   return_value=["sonny_one/apl_targets/other.py"]):
            with self.assertRaises(ValueError):
                validate_model_proposal(task(), proposal())

    def test_rejects_multiple_experimental_paths(self):
        with patch("sonny_one.development_controller.model_proposal_adapter.validate_patch",
                   return_value=["sonny_one/apl_targets/offline_strategy.py",
                                 "sonny_one/apl_targets/other.py"]):
            with self.assertRaises(ValueError):
                validate_model_proposal(task(), proposal())

    def test_rejects_nonallowlisted_task(self):
        with self.assertRaises(PermissionError):
            validate_model_proposal(task("DEV-001"), proposal())

    def test_rejects_unapproved_task(self):
        with self.assertRaises(PermissionError):
            validate_model_proposal({**task(), "requires_approval": True}, proposal())

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValueError):
            validate_model_proposal(task(), {**proposal(), "command": "sh"})

    def test_rejects_wrong_task_id(self):
        with self.assertRaises(ValueError):
            validate_model_proposal(task(), {**proposal(), "task_id": "OTHER-001"})

    def test_rejects_oversized_patch(self):
        with self.assertRaises(ValueError):
            validate_model_proposal(task(), {"task_id": "RES-001",
                                             "patch_text": "a" * 32769})

    def test_agent_does_not_advance_after_model_proposal(self):
        q = {"version": 1, "tasks": [task()]}
        with patch("sonny_one.development_controller.model_proposal_adapter.validate_patch"):
            adapter = ModelProposalAdapter(lambda t: proposal())
            result = DevelopmentAgent(adapter).run(q, authorized=True)
        self.assertEqual(result.tasks_completed, 0)
        self.assertEqual(q["tasks"][0]["state"], "ready")

    def test_unauthorized_agent_does_not_invoke_model(self):
        calls = []
        adapter = ModelProposalAdapter(lambda t: calls.append(t))
        result = DevelopmentAgent(adapter).run({"version": 1, "tasks": [task()]},
                                               authorized=False)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
