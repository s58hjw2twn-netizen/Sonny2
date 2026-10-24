import io
import json
import unittest
from unittest.mock import patch

from sonny_one.development_controller.local_model_preflight import check_local_model


class Response:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode())

    def read(self, size):
        return self.stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class PreflightTests(unittest.TestCase):
    def run_with(self, payload, name="coder:small"):
        class Opener:
            def open(self, request, timeout):
                self.request = request
                return Response(payload)
        opener = Opener()
        with patch("sonny_one.development_controller.local_model_preflight.build_opener",
                   return_value=opener):
            result = check_local_model(name, enabled=True)
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertEqual(opener.request.full_url, "http://127.0.0.1:11434/api/tags")
        return result

    def test_detects_installed_model(self):
        result = self.run_with({"models": [{"name": "coder:small"}]})
        self.assertTrue(result["available"])
        self.assertFalse(result["inference_tested"])

    def test_missing_model(self):
        self.assertFalse(self.run_with({"models": []})["available"])

    def test_requires_opt_in(self):
        with self.assertRaises(PermissionError):
            check_local_model("coder:small")

    def test_rejects_bad_name(self):
        with self.assertRaises(ValueError):
            check_local_model("http://remote.example", enabled=True)

    def test_rejects_malformed_response(self):
        with self.assertRaises(ValueError):
            self.run_with({"models": "invalid"})

    def test_rejects_invalid_timeout(self):
        with self.assertRaises(ValueError):
            check_local_model("coder:small", enabled=True, timeout=100)


if __name__ == "__main__":
    unittest.main()
