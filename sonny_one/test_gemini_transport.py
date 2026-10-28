"""Offline transport tests: no external requests, credentials or billing."""
import json
import unittest
from unittest.mock import patch

from sonny_one.gemini_transport import GeminiTransport
from sonny_one.inference import InferenceFailure, InferenceTimeout, Request


class FakeResponse:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        return self.data[:n]


class GeminiTransportTests(unittest.TestCase):
    def test_success_uses_https_and_header_not_url(self):
        seen = {}

        def opener(req, **kwargs):
            seen["url"] = req.full_url
            seen["key"] = req.get_header("X-goog-api-key")
            seen["timeout"] = kwargs["timeout"]
            seen["body"] = json.loads(req.data)
            return FakeResponse(json.dumps({"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "Hello!"}]}}]}).encode())

        transport = GeminiTransport(api_key="example-test-key", opener=opener)
        response = transport.generate(Request("Hello", timeout_seconds=3))
        self.assertEqual(response.text, "Hello!")
        self.assertFalse(response.demo)
        self.assertTrue(seen["url"].startswith("https://generativelanguage.googleapis.com/"))
        self.assertNotIn("example-test-key", seen["url"])
        self.assertEqual(seen["key"], "example-test-key")
        self.assertEqual(seen["timeout"], 3)
        self.assertEqual(seen["body"]["contents"][0]["parts"][0]["text"], "Hello")

    def test_timeout_is_sanitized(self):
        def opener(*args, **kwargs):
            raise TimeoutError("secret connection details")
        with self.assertRaises(InferenceTimeout) as caught:
            GeminiTransport(api_key="example-test-key", opener=opener).generate(Request("Hello"))
        self.assertNotIn("secret", str(caught.exception))

    def test_rejects_large_and_invalid_responses(self):
        for data in (b"x" * 65537, b"not json", b"{}", b'{"candidates": []}'):
            with self.subTest(length=len(data)), self.assertRaises(InferenceFailure):
                GeminiTransport(api_key="example-test-key", opener=lambda *a, **k: FakeResponse(data)).generate(Request("Hello"))

    def test_rejects_invalid_configuration(self):
        for key in ("", "short", "with spaces inside"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                GeminiTransport(api_key=key)
        with self.assertRaises(ValueError):
            GeminiTransport(api_key="example-test-key", model_id="../../bad")


if __name__ == "__main__":
    unittest.main()
