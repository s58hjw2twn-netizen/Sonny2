import unittest

from sonny_one.development_controller.development_agent import DevelopmentAgent


def queue():
    return {"version": 1, "tasks": [
        {"id": "APP-101", "track": "app", "title": "Add safe test", "state": "ready", "priority": 1, "requires_approval": False},
        {"id": "APP-102", "track": "app", "title": "Add safe docs", "state": "ready", "priority": 2, "requires_approval": False},
        {"id": "APP-103", "track": "app", "title": "Production deployment", "state": "ready", "priority": 3, "requires_approval": True},
    ]}


class DevelopmentAgentTests(unittest.TestCase):
    def test_no_authorization_means_no_execution(self):
        calls = []
        q = queue()
        result = DevelopmentAgent(lambda task: calls.append(task) or True).run(q)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(calls, [])
        self.assertEqual(q["tasks"][0]["state"], "ready")

    def test_no_executor_means_no_execution(self):
        self.assertEqual(DevelopmentAgent().run(queue(), authorized=True).status, "blocked")

    def test_verified_tasks_advance_and_sensitive_tasks_do_not(self):
        q = queue()
        result = DevelopmentAgent(lambda task: True).run(q, authorized=True, max_tasks=10)
        self.assertEqual(result.tasks_completed, 2)
        self.assertEqual(result.status, "idle")
        self.assertEqual(q["tasks"][2]["state"], "ready")

    def test_failed_executor_stops_without_advancing(self):
        q = queue()
        result = DevelopmentAgent(lambda task: False).run(q, authorized=True)
        self.assertEqual(result.status, "failed")
        self.assertEqual(q["tasks"][0]["state"], "ready")

    def test_exception_stops_without_advancing(self):
        q = queue()
        def broken(task):
            raise RuntimeError("unavailable")
        self.assertEqual(DevelopmentAgent(broken).run(q, authorized=True).status, "failed")
        self.assertEqual(q["tasks"][0]["state"], "ready")

    def test_limit_is_enforced(self):
        q = queue()
        result = DevelopmentAgent(lambda task: True).run(q, authorized=True, max_tasks=1)
        self.assertEqual(result.tasks_completed, 1)
        self.assertEqual(q["tasks"][1]["state"], "ready")

    def test_bad_limit_rejected(self):
        with self.assertRaises(ValueError):
            DevelopmentAgent().run(queue(), max_tasks=0, authorized=True)


if __name__ == "__main__":
    unittest.main()
