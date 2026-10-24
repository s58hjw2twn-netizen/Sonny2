"""Offline contract tests for the dormant local Ollama adapter."""
import io
import json
import unittest
from unittest.mock import patch

from sonny_one.inference import InferenceFailure, Request
from sonny_one.ollama_local import LocalOllamaProvider


class FakeHTTP:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, count):
        return self.data[:count]


class OllamaLocalTests(unittest.TestCase):
    def test_loopback_only(self):
        for address in ("http://192.168.1.2:11434", "https://localhost:11434",
                        "http://127.0.0.1:9999", "http://evil.invalid"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                LocalOllamaProvider("small", endpoint=address)

    def test_model_name_rejects_url_and_control_characters(self):
        for model in ("", "../../secret", "model\nX", "model name"):
            with self.subTest(model=model), self.assertRaises(ValueError):
                LocalOllamaProvider(model)

    def test_valid_response(self):
        provider = LocalOllamaProvider("test:1b")
        payload = json.dumps({"response": "Hello from local Sonny", "done": True}).encode()
        with patch.object(provider._opener, "open", return_value=FakeHTTP(payload)) as opener:
            result = provider.generate(Request("hi", timeout_seconds=2))
        self.assertEqual(result.text, "Hello from local Sonny")
        self.assertEqual(result.model_id, "test:1b")
        args, kwargs = opener.call_args
        self.assertEqual(kwargs["timeout"], 2)
        self.assertEqual(json.loads(args[0].data)["stream"], False)

    def test_rejects_incomplete_or_large_responses(self):
        provider = LocalOllamaProvider("test")
        for payload in (b'{"response":"partial","done":false}', b"not-json",
                        b"x" * 65537):
            with self.subTest(payload=payload[:20]):
                with patch.object(provider._opener, "open", return_value=FakeHTTP(payload)):
                    with self.assertRaises(InferenceFailure):
                        provider.generate(Request("hi"))


if __name__ == "__main__":
    unittest.main()
