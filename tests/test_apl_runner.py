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


    def test_suite_fingerprint_changes_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "test_sample.py").write_text("assert True")
            before = runner.suite_fingerprint(p)
            (p / "test_sample.py").write_text("assert False")
            self.assertNotEqual(before, runner.suite_fingerprint(p))

    def test_suite_fingerprint_stable_across_creation_order(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for name in ("b.py", "a.py"):
                (Path(a) / name).write_text(name)
            for name in ("a.py", "b.py"):
                (Path(b) / name).write_text(name)
            self.assertEqual(runner.suite_fingerprint(Path(a)),
                             runner.suite_fingerprint(Path(b)))

    def test_suite_fingerprint_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "test.py").write_text("pass")
            (p / "alias.py").symlink_to(p / "test.py")
            with self.assertRaises(ValueError):
                runner.suite_fingerprint(p)


if __name__ == "__main__":
    unittest.main()
