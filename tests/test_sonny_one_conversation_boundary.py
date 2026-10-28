import unittest
from sonny_one.conversation_boundary import validate_conversation_payload


class ConversationBoundaryTests(unittest.TestCase):
    def test_valid(self):
        result = validate_conversation_payload(" Hello ", ["approved"])
        self.assertEqual(result["message"], "Hello")
        self.assertFalse(result["persistent_storage_authorized"])
        self.assertFalse(result["external_provider_authorized"])

    def test_empty_message_rejected(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("   ", [])

    def test_long_message_rejected(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("x" * 4001, [])

    def test_excess_memories_rejected(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello", ["ok"] * 51)

    def test_invalid_memory_rejected(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello", [""])

    def test_total_budget_rejected(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello", ["memory"], max_total_chars=6)

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello", [], max_total_chars=True)

    def test_goal_counts_toward_budget(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello", ["memory"], max_total_chars=11, goal="goal")

    def test_control_character_rejected_in_message(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello\x00world", [])

    def test_control_character_rejected_in_memory(self):
        with self.assertRaises(ValueError):
            validate_conversation_payload("hello", ["approved\x1bmemory"])

    def test_ordinary_newline_allowed(self):
        result = validate_conversation_payload("hello\nworld", [])
        self.assertEqual(result["message"], "hello\nworld")

    def test_live_chat_route_rejects_total_budget(self):
        from fastapi.testclient import TestClient
        from sonny_one.web_app import app
        client = TestClient(app)
        response = client.post("/api/chat", json={
            "message": "hello",
            "memories": ["x" * 500] * 25
        })
        self.assertEqual(response.status_code, 422)

    def test_demo_inference_rejects_total_budget(self):
        from fastapi.testclient import TestClient
        from sonny_one.web_app import app
        client = TestClient(app)
        response = client.post("/api/inference/demo", json={
            "message": "hello",
            "memories": ["x" * 500] * 25
        })
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
