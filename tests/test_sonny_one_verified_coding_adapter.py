import unittest
from unittest.mock import patch

from sonny_one.development_controller.development_agent import DevelopmentAgent
from sonny_one.development_controller.verified_coding_adapter import VerifiedCodingAdapter

PARENT = "a" * 40
COMMIT = "b" * 40


def queue():
    return {"version": 1, "tasks": [
        {"id": "DEV-001", "track": "app", "title": "Safe coding task",
         "state": "ready", "priority": 1, "requires_approval": False}
    ]}


def receipt():
    return {"task_id": "DEV-001", "parent_sha": PARENT, "commit_sha": COMMIT,
            "branch": "research/apl-001", "test_run_id": "101",
            "test_conclusion": "success", "policy_run_id": "102",
            "policy_conclusion": "success", "independent_verification": True}


class VerifiedCodingAdapterTests(unittest.TestCase):
    def test_verified_receipt_advances_task(self):
        q = queue()
        with patch("sonny_one.development_controller.verified_coding_adapter.verify_github_receipt",
                   return_value={"verified": True, "commit_sha": COMMIT, "task_id": "DEV-001"}) as verifier:
            adapter = VerifiedCodingAdapter(
                produce_receipt=lambda task: receipt(),
                fetch_json=lambda url: {}, parent_sha=PARENT)
            result = DevelopmentAgent(adapter).run(q, authorized=True)
        self.assertEqual(result.tasks_completed, 1)
        self.assertEqual(q["tasks"][0]["state"], "done")
        self.assertEqual(adapter.parent_sha, COMMIT)
        verifier.assert_called_once()

    def test_rejected_receipt_never_advances(self):
        q = queue()
        with patch("sonny_one.development_controller.verified_coding_adapter.verify_github_receipt",
                   side_effect=ValueError("CI mismatch")):
            adapter = VerifiedCodingAdapter(
                produce_receipt=lambda task: receipt(),
                fetch_json=lambda url: {}, parent_sha=PARENT)
            result = DevelopmentAgent(adapter).run(q, authorized=True)
        self.assertEqual(result.status, "failed")
        self.assertEqual(q["tasks"][0]["state"], "ready")
        self.assertEqual(adapter.parent_sha, PARENT)

    def test_missing_coding_producer_rejected(self):
        with self.assertRaises(TypeError):
            VerifiedCodingAdapter(produce_receipt=None,
                                  fetch_json=lambda url: {}, parent_sha=PARENT)

    def test_no_execution_without_authorization(self):
        calls = []
        adapter = VerifiedCodingAdapter(
            produce_receipt=lambda task: calls.append(task),
            fetch_json=lambda url: {}, parent_sha=PARENT)
        result = DevelopmentAgent(adapter).run(queue(), authorized=False)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
