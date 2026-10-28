"""Development controller regression tests: no automatic execution or promotion."""
import unittest
from sonny_one.development_controller.controller import plan, validate_queue


def task(ident, track="app", priority=1, approval=False, state="ready", title="Test task"):
    return {"id": ident, "track": track, "priority": priority,
            "requires_approval": approval, "state": state, "title": title}


class ControllerTests(unittest.TestCase):
    def test_committed_task_queue_is_valid(self):
        import json
        from pathlib import Path
        queue_path = Path(__file__).resolve().parents[1] / "sonny_one" / "development_controller" / "tasks.json"
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        result = plan(queue)
        self.assertIsNotNone(result["next_task"])
        self.assertFalse(result["execution_started"])

    def test_priorities(self):
        result = plan({"version": 1, "tasks": [task("B", priority=2), task("A")]})
        self.assertEqual(result["next_task"]["id"], "A")

    def test_approval_never_runs(self):
        result = plan({"version": 1, "tasks": [task("A", approval=True)]})
        self.assertIsNone(result["next_task"])
        self.assertEqual(result["approval_required"], ["A"])

    def test_no_autonomous_execution_claim(self):
        result = plan({"version": 1, "tasks": [task("A")]})
        self.assertFalse(result["execution_started"])
        self.assertFalse(result["coding_agent_connected"])

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate_queue({"version": 1, "tasks": [task("A"), task("A")]})

    def test_sensitive_title_requires_approval(self):
        with self.assertRaises(ValueError):
            validate_queue({"version": 1, "tasks": [task("A", title="Deploy production")]})

    def test_invalid_priority(self):
        with self.assertRaises(ValueError):
            validate_queue({"version": 1, "tasks": [task("A", priority=True)]})

    def test_blocked_tasks_not_selected(self):
        result = plan({"version": 1, "tasks": [task("A", state="blocked")]})
        self.assertIsNone(result["next_task"])


if __name__ == "__main__":
    unittest.main()
