"""End-to-end APL orchestration against a disposable Git repo and fake Docker."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sonny_one.apl.runner import evaluate


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          check=True, text=True, capture_output=True).stdout.strip()


class TestAPLEvaluationFlow(unittest.TestCase):
    def test_clean_baseline_and_candidate_yield_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            target = source / "sonny_one" / "apl_targets"
            target.mkdir(parents=True)
            example = target / "example.py"
            example.write_text("value = 1\n")
            git(source, "init", "-q")
            git(source, "config", "user.email", "apl@example.invalid")
            git(source, "config", "user.name", "APL Test")
            git(source, "add", ".")
            git(source, "commit", "-qm", "baseline")
            revision = git(source, "rev-parse", "HEAD")
            example.write_text("value = 2\n")
            patch_file = root / "candidate.diff"
            patch_file.write_text(git(source, "diff", "--", "sonny_one/apl_targets/example.py") + "\n")
            git(source, "checkout", "--", "sonny_one/apl_targets/example.py")
            trusted, heldout = root / "trusted", root / "heldout"
            trusted.mkdir()
            heldout.mkdir()
            (trusted / "test_basic.py").write_text("def test_basic(): assert True\n")
            (heldout / "test_hidden.py").write_text("def test_hidden(): assert True\n")
            calls = []
            def fake_docker(image, workspace, suite, timeout):
                calls.append((Path(workspace).name, Path(suite).name))
                return {"exit_code": 0, "stdout_tail": "", "stderr_tail": ""}
            with patch("sonny_one.apl.runner.docker_test", side_effect=fake_docker):
                result = evaluate(source, revision, patch_file, trusted, heldout,
                                  "runner@sha256:" + "a" * 64, root / "ledger.jsonl")
            self.assertEqual(result["status"], "ELIGIBLE_FOR_HUMAN_REVIEW")
            self.assertEqual(result["promotion"], "FORBIDDEN")
            self.assertFalse(result["comparison"]["improvement_proven"])
            self.assertEqual(calls, [("baseline", "trusted"), ("baseline", "heldout"),
                                     ("workspace", "trusted"), ("workspace", "heldout")])

    def test_baseline_failure_prevents_review_eligibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            target = source / "sonny_one" / "apl_targets"
            target.mkdir(parents=True)
            example = target / "example.py"
            example.write_text("old\n")
            git(source, "init", "-q")
            git(source, "config", "user.email", "apl@example.invalid")
            git(source, "config", "user.name", "APL Test")
            git(source, "add", ".")
            git(source, "commit", "-qm", "baseline")
            revision = git(source, "rev-parse", "HEAD")
            example.write_text("new\n")
            patch_file = root / "candidate.diff"
            patch_file.write_text(git(source, "diff") + "\n")
            git(source, "checkout", "--", ".")
            trusted, heldout = root / "trusted", root / "heldout"
            trusted.mkdir()
            heldout.mkdir()
            def fake_docker(image, workspace, suite, timeout):
                code = 1 if Path(workspace).name == "baseline" else 0
                return {"exit_code": code, "stdout_tail": "", "stderr_tail": ""}
            with patch("sonny_one.apl.runner.docker_test", side_effect=fake_docker):
                result = evaluate(source, revision, patch_file, trusted, heldout,
                                  "runner@sha256:" + "a" * 64, root / "ledger.jsonl")
            self.assertEqual(result["status"], "REJECTED")
            self.assertIn("Baseline suite failed", result["error"])


if __name__ == "__main__":
    unittest.main()
