"""Tests for the provider-neutral inference boundary."""
import unittest

from sonny_one.inference import (
    InferenceFailure, OfflineProvider, Request, Response, generate,
)


class InferenceTests(unittest.TestCase):
    def test_offline(self):
        response = generate(OfflineProvider(), "hello")
        self.assertTrue(response.demo)
        self.assertEqual(response.model_id, "offline-demo-v1")

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            Request(" ")

    def test_long_input(self):
        with self.assertRaises(ValueError):
            Request("x" * 8001)

    def test_failure_is_sanitized(self):
        class Broken:
            def generate(self, request):
                raise RuntimeError("private provider details")
        with self.assertRaisesRegex(InferenceFailure, "^Inference unavailable$"):
            generate(Broken(), "hello")

    def test_wrong_type_rejected(self):
        class Broken:
            def generate(self, request):
                return {"text": "hello"}
        with self.assertRaisesRegex(InferenceFailure, "Invalid provider response"):
            generate(Broken(), "hello")

    def test_blank_text_rejected(self):
        class Broken:
            def generate(self, request):
                return Response(" ", "demo")
        with self.assertRaisesRegex(InferenceFailure, "Invalid provider response"):
            generate(Broken(), "hello")

    def test_blank_model_rejected(self):
        class Broken:
            def generate(self, request):
                return Response("hello", " ")
        with self.assertRaisesRegex(InferenceFailure, "Invalid model identifier"):
            generate(Broken(), "hello")


if __name__ == "__main__":
    unittest.main()
