"""Confidential holdout requests must fail before any candidate execution."""
import unittest
from unittest.mock import patch
from sonny_one.apl.runner import evaluate


class ConfidentialHoldoutGateTests(unittest.TestCase):
    @patch("sonny_one.apl.runner.preflight_docker_image")
    @patch("sonny_one.apl.runner.execute")
    def test_confidential_holdout_fails_closed(self, execute, preflight):
        with self.assertRaisesRegex(RuntimeError, "Confidential holdout"):
            evaluate("/nonexistent/source", "a" * 40, "/nonexistent/patch",
                     "/nonexistent/trusted", "/nonexistent/heldout",
                     "python@sha256:" + "b" * 64, "/nonexistent/ledger",
                     require_confidential_holdout=True)
        execute.assert_not_called()
        preflight.assert_not_called()


if __name__ == "__main__":
    unittest.main()
