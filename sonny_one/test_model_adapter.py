"""Model adapter tests use a local fake transport; no network calls."""
import unittest

from sonny_one.inference import InferenceFailure, Request, generate
from sonny_one.model_adapter import ModelEndpoint, TransportAdapter


class ModelAdapterTests(unittest.TestCase):
    def test_fake_transport(self):
        seen = []
        def fake(prompt, timeout):
            seen.append((prompt, timeout))
            return "local answer"
        result = generate(TransportAdapter(ModelEndpoint("local-test"), fake), "hello")
        self.assertEqual(seen, [("hello", 20.0)])
        self.assertEqual(result.text, "local answer")
        self.assertFalse(result.demo)

    def test_output_limit(self):
        adapter = TransportAdapter(ModelEndpoint("local-test", 3), lambda p, t: "long")
        with self.assertRaises(InferenceFailure):
            generate(adapter, "hello")

    def test_empty_response(self):
        adapter = TransportAdapter(ModelEndpoint("local-test"), lambda p, t: "")
        with self.assertRaises(InferenceFailure):
            generate(adapter, "hello")

    def test_control_character_rejected(self):
        adapter = TransportAdapter(ModelEndpoint("local-test"), lambda p, t: "ok" + chr(0))
        with self.assertRaises(InferenceFailure):
            generate(adapter, "hello")

    def test_newline_allowed(self):
        adapter = TransportAdapter(ModelEndpoint("local-test"), lambda p, t: "line 1" + chr(10) + "line 2")
        self.assertIn(chr(10), generate(adapter, "hello").text)

    def test_bad_model_id(self):
        with self.assertRaises(ValueError):
            ModelEndpoint(" ")

    def test_bad_output_limit(self):
        with self.assertRaises(ValueError):
            ModelEndpoint("local-test", 16001)

    def test_transport_required(self):
        with self.assertRaises(TypeError):
            TransportAdapter(ModelEndpoint("local-test"), None)

    def test_transport_receives_deadline(self):
        adapter = TransportAdapter(ModelEndpoint("local-test"), lambda p, t: str(t))
        self.assertEqual(adapter.generate(Request("hello", timeout_seconds=3.5)).text, "3.5")


if __name__ == "__main__":
    unittest.main()
