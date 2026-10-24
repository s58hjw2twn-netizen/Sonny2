"""Tests for the provider-neutral inference boundary."""
import unittest

from sonny_one.inference import (
    InferenceFailure, InferenceTimeout, OfflineProvider, Request, Response, generate,
)


class InferenceTests(unittest.TestCase):
    def test_offline(self):
        response = generate(OfflineProvider(), "hello")
        self.assertTrue(response.demo)
        self.assertEqual(response.model_id, "offline-demo-v1")

    def test_timeout_budget_validation(self):
        for timeout in (0, -1, 121, True, "10"):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                Request("hello", timeout_seconds=timeout)

    def test_timeout_sanitized(self):
        class Slow:
            def generate(self, request):
                raise TimeoutError("private timeout details")
        with self.assertRaisesRegex(InferenceTimeout, "^Inference timed out$"):
            generate(Slow(), "hello")

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

    def test_oversized_output_rejected(self):
        class Oversized:
            def generate(self, request):
                return Response("x" * 16001, "test")
        with self.assertRaisesRegex(InferenceFailure, "Invalid provider response"):
            generate(Oversized(), "hello")

    def test_invalid_demo_flag_rejected(self):
        class Invalid:
            def generate(self, request):
                return Response("hello", "test", "false")
        with self.assertRaisesRegex(InferenceFailure, "Invalid provider response"):
            generate(Invalid(), "hello")

    def test_blank_model_rejected(self):
        class Broken:
            def generate(self, request):
                return Response("hello", " ")
        with self.assertRaisesRegex(InferenceFailure, "Invalid model identifier"):
            generate(Broken(), "hello")


if __name__ == "__main__":
    unittest.main()
