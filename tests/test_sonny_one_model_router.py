"""Offline deterministic tests for the model boundary."""
import unittest
from sonny_one.model_router import ModelOption, ModelRouter

class Fake:
    def __init__(self, response="ok"): self.response = response
    def generate(self, *, system, user): return self.response

class RouterTests(unittest.TestCase):
    def test_lowest_cost(self):
        r = ModelRouter([ModelOption("paid", Fake(), frozenset({"chat"}), 3),
                         ModelOption("free", Fake(), frozenset({"chat"}), 0)])
        self.assertEqual(r.select("chat").name, "free")
    def test_paid_blocked_by_default(self):
        r = ModelRouter([ModelOption("paid", Fake(), frozenset({"chat"}), 1)])
        with self.assertRaises(LookupError): r.select("chat")
    def test_disabled_blocked(self):
        r = ModelRouter([ModelOption("off", Fake(), frozenset({"chat"}), enabled=False)])
        with self.assertRaises(LookupError): r.select("chat")
    def test_preferred_must_be_eligible(self):
        r = ModelRouter([ModelOption("a", Fake(), frozenset({"chat"}))])
        with self.assertRaises(LookupError): r.select("chat", preferred="b")
    def test_generate_returns_provenance(self):
        r = ModelRouter([ModelOption("local", Fake("hello"), frozenset({"chat"}))])
        self.assertEqual(r.generate("chat", system="s", user="u"), ("hello", "local"))
    def test_reject_duplicates(self):
        with self.assertRaises(ValueError):
            ModelRouter([ModelOption("x", Fake(), frozenset({"chat"})),
                         ModelOption("x", Fake(), frozenset({"chat"}))])
    def test_reject_negative_budget(self):
        with self.assertRaises(ValueError): ModelRouter([], max_cost_units=-1)
    def test_reject_wrong_response_type(self):
        r = ModelRouter([ModelOption("x", Fake(None), frozenset({"chat"}))])
        with self.assertRaises(TypeError): r.generate("chat", system="s", user="u")

if __name__ == "__main__":
    unittest.main()
