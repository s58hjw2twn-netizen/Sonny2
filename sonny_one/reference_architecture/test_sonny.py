"""Isolated reference tests; run python -m unittest discover -s sonny_one/reference_architecture -p 'test_*.py'."""
import unittest
from sonny_reference import Sonny, ConsentMemory, SelfModel

class SonnyReferenceTests(unittest.TestCase):
    def test_offline_response(self):
        self.assertIn("No external AI model", Sonny().respond("hello"))
    def test_memory_requires_consent(self):
        with self.assertRaises(PermissionError):
            ConsentMemory().remember("a", "b")
    def test_memory_deletion(self):
        m = ConsentMemory(enabled=True)
        m.remember("a", "b")
        m.forget("a")
        self.assertNotIn("a", m.facts)
    def test_prediction_bounds(self):
        with self.assertRaises(ValueError):
            SelfModel().record_prediction("task", 1.1)
    def test_empty_input(self):
        with self.assertRaises(ValueError):
            Sonny().respond(" ")
    def test_nonstring_input(self):
        with self.assertRaises(ValueError):
            Sonny().respond(None)
    def test_no_implicit_memory_prompt_injection(self):
        m = ConsentMemory(enabled=True)
        m.remember("private", "SECRET_SENTINEL")
        self.assertNotIn("SECRET_SENTINEL", Sonny(memory=m).respond("hello"))

if __name__ == "__main__":
    unittest.main()
