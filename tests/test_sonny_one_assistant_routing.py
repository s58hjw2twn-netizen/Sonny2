"""Offline assistant integration tests with deterministic fakes."""
import unittest
from types import SimpleNamespace
from sonny_one.assistant import SonnyOneAssistant
from sonny_one.model_router import ModelOption, ModelRouter

class Fake:
    def __init__(self, value="ok"): self.value = value
    def generate(self, *, system, user): return self.value

class Runtime:
    def inspect(self, user_id):
        return SimpleNamespace(recalled=["approved fact"], identity="sonny")

class AssistantRoutingTests(unittest.TestCase):
    def test_router_returns_model_provenance(self):
        assistant = SonnyOneAssistant(Runtime(), ModelRouter([
            ModelOption("local", Fake(), frozenset({"chat"}), approved=True, license_verified=True, available=True)]))
        self.assertEqual(assistant.reply("u", "hello").model_name, "local")
    def test_legacy_model_unchanged(self):
        assistant = SonnyOneAssistant(Runtime(), Fake())
        self.assertIsNone(assistant.reply("u", "hello").model_name)
    def test_no_paid_model_without_budget(self):
        assistant = SonnyOneAssistant(Runtime(), ModelRouter([
            ModelOption("paid", Fake(), frozenset({"chat"}), 1)]))
        with self.assertRaises(LookupError): assistant.reply("u", "hello")
    def test_legacy_preference_rejected(self):
        assistant = SonnyOneAssistant(Runtime(), Fake())
        with self.assertRaises(ValueError):
            assistant.reply("u", "hello", preferred_model="other")
    def test_invalid_legacy_model_response(self):
        assistant = SonnyOneAssistant(Runtime(), Fake(None))
        with self.assertRaises(TypeError): assistant.reply("u", "hello")

if __name__ == "__main__":
    unittest.main()
