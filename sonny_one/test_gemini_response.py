"""Contract tests for the unconnected Gemini parser."""
import unittest
from sonny_one.gemini_response import parse_gemini_response


class GeminiResponseTests(unittest.TestCase):
    def test_valid_response(self):
        payload = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "Hello "}, {"text": "from Sonny"}]}}]}
        response = parse_gemini_response(payload)
        self.assertEqual(response.text, "Hello from Sonny")
        self.assertFalse(response.demo)

    def test_rejects_blocked_or_truncated(self):
        for reason in ("MAX_TOKENS", "SAFETY", None):
            payload = {"candidates": [{"finishReason": reason, "content": {"parts": [{"text": "partial"}]}}]}
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                parse_gemini_response(payload)

    def test_rejects_invalid_payloads(self):
        for payload in (None, {}, {"candidates": []}, {"candidates": [None]},
                        {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {}}]}}]}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_gemini_response(payload)


if __name__ == "__main__":
    unittest.main()
