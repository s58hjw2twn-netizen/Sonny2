"""Runner orchestration tests with fake git/docker; no Docker or network required."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from sonny_one.apl import runner


class TestRunnerGuardrails(unittest.TestCase):
    def test_rejects_unpinned_image_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for name in ("source", "trusted", "heldout"):
                (p / name).mkdir()
            (p / "candidate.diff").write_text("not relevant")
            with patch.object(runner, "execute") as execute:
                with self.assertRaises(ValueError):
                    runner.evaluate(p / "source", "a" * 40, p / "candidate.diff",
                                    p / "trusted", p / "heldout", "python:latest",
                                    p / "ledger")
                execute.assert_not_called()

    def test_rejects_test_suite_inside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "source" / "tests").mkdir(parents=True)
            (p / "heldout").mkdir()
            (p / "candidate.diff").write_text("not relevant")
            with self.assertRaises(ValueError):
                runner.evaluate(p / "source", "a" * 40, p / "candidate.diff",
                                p / "source" / "tests", p / "heldout",
                                "runner@sha256:" + "a" * 64, p / "ledger")


if __name__ == "__main__":
    unittest.main()
