"""Tests for Gemini request caps and validation."""
import unittest
from sonny_one.gemini_request import GeminiRequestConfig, build_gemini_request


class GeminiRequestTests(unittest.TestCase):
    def test_bounded_payload(self):
        payload = build_gemini_request("  Hello Sonny  ")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "Hello Sonny")
        self.assertLessEqual(payload["generationConfig"]["maxOutputTokens"], 512)

    def test_rejects_oversize_or_blank(self):
        for message in (" ", "x" * 4001, None):
            with self.subTest(message=str(message)[:15]), self.assertRaises(ValueError):
                build_gemini_request(message)

    def test_rejects_invalid_caps(self):
        for cap in (0, 513, True):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                GeminiRequestConfig(max_output_tokens=cap)

    def test_rejects_nonfinite_temperature(self):
        for temperature in (float("nan"), float("inf"), -1):
            with self.subTest(temperature=temperature), self.assertRaises(ValueError):
                GeminiRequestConfig(temperature=temperature)


if __name__ == "__main__":
    unittest.main()
