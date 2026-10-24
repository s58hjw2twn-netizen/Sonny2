import unittest
from unittest.mock import patch

from sonny_one.development_controller.development_agent import DevelopmentAgent
from sonny_one.development_controller.offline_proposal_engine import OfflineProposalEngine


def task(task_id="RES-001"):
    return {"id": task_id, "track": "research", "title": "Offline APL proposal",
            "state": "ready", "priority": 1, "requires_approval": False}


def queue():
    return {"version": 1, "tasks": [task()]}


class OfflineProposalEngineTests(unittest.TestCase):
    def test_generates_review_only_proposal(self):
        engine = OfflineProposalEngine(".", max_candidates=1)
        fake = {"proposals": [{"candidate_id": "a" * 64}],
                "promotion": "FORBIDDEN", "ready_for_runner": False}
        with patch("sonny_one.development_controller.offline_proposal_engine.prepare_bundle",
                   return_value=fake) as generator:
            report = engine.propose(task())
        self.assertEqual(report["proposal_count"], 1)
        self.assertFalse(report["committed"])
        self.assertFalse(report["development_task_completed"])
        generator.assert_called_once()

    def test_proposal_does_not_complete_agent_task(self):
        engine = OfflineProposalEngine(".")
        q = queue()
        with patch("sonny_one.development_controller.offline_proposal_engine.prepare_bundle",
                   return_value={"proposals": [{}]}):
            result = DevelopmentAgent(engine).run(q, authorized=True)
        self.assertEqual(result.tasks_completed, 0)
        self.assertEqual(q["tasks"][0]["state"], "ready")

    def test_unapproved_task_rejected(self):
        engine = OfflineProposalEngine(".")
        with self.assertRaises(PermissionError):
            engine.propose({**task(), "requires_approval": True})

    def test_nonresearch_task_rejected(self):
        engine = OfflineProposalEngine(".")
        with self.assertRaises(PermissionError):
            engine.propose(task("DEV-001"))

    def test_bad_budget_rejected(self):
        with self.assertRaises(ValueError):
            OfflineProposalEngine(".", max_candidates=11)

    def test_agent_without_authorization_never_calls_generator(self):
        engine = OfflineProposalEngine(".")
        with patch("sonny_one.development_controller.offline_proposal_engine.prepare_bundle") as generator:
            result = DevelopmentAgent(engine).run(queue(), authorized=False)
        self.assertEqual(result.status, "blocked")
        generator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
