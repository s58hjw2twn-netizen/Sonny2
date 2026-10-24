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


if __name__ == "__main__":
    unittest.main()
