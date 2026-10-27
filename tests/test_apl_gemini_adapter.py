"""Trusted Gemini APL adapter tests; all provider calls mocked."""
import os
import unittest
from unittest.mock import patch

from sonny_one.apl.gemini_adapter import propose_with_gemini

REV = "a" * 40
TARGET = "sonny_one/apl_targets/offline_strategy.py"
DIFF = (f"diff --git a/{TARGET} b/{TARGET}\n"
        f"--- a/{TARGET}\n+++ b/{TARGET}\n"
        "@@ -1 +1 @@\n-old\n+new\n")


class GeminiAdapterTests(unittest.TestCase):
    def call_adapter(self, **changes):
        args = dict(source_text="old\n", target_path=TARGET,
                    objective="Fix the example", base_revision=REV)
        args.update(changes)
        return propose_with_gemini(**args)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-unit-test-key"})
    @patch("sonny.gemini_provider.generate_gemini", return_value=DIFF)
    def test_validated_proposal_not_executed(self, generate):
        result = self.call_adapter()
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertFalse(result["tests_executed"])
        self.assertFalse(result["model_identity_authenticated"])
        self.assertEqual(result["target_paths"], [TARGET])
        self.assertTrue(result["provider_response_authenticated_by_transport"])
        self.assertEqual(generate.call_count, 1)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-unit-test-key"})
    @patch("sonny.gemini_provider.generate_gemini", return_value=DIFF.replace(
        TARGET, "sonny/app.py"))
    def test_rejects_unapproved_diff(self, generate):
        with self.assertRaises(ValueError):
            self.call_adapter()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-unit-test-key"})
    @patch("sonny.gemini_provider.generate_gemini")
    def test_rejects_invalid_inputs_before_network(self, generate):
        for kwargs in ({"base_revision": "main"},
                       {"target_path": "sonny/app.py"},
                       {"source_text": "x" * 16001},
                       {"objective": ""}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.call_adapter(**kwargs)
        generate.assert_not_called()

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    @patch("sonny.gemini_provider.generate_gemini")
    def test_missing_key_fails_closed(self, generate):
        with self.assertRaises(RuntimeError):
            self.call_adapter()
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
