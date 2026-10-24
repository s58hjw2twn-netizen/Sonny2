import hashlib
import subprocess
from unittest.mock import patch

import pytest

from sonny.paired_syntax_runner import run_paired_syntax_checks

IMAGE = "python:3.11-slim@sha256:" + "a" * 64


def workspaces(tmp_path):
    base = tmp_path / "base"
    candidate = tmp_path / "candidate"
    for folder, value in ((base, "1"), (candidate, "2")):
        (folder / "sonny").mkdir(parents=True)
        (folder / "sonny" / "example.py").write_text("value = " + value + "\n")
    return base, candidate


def test_pair_detects_regression_and_never_approves_commit(tmp_path):
    base, candidate = workspaces(tmp_path)
    outcomes = [
        subprocess.CompletedProcess([], 0, b"", b""),
        subprocess.CompletedProcess([], 1, b"", b"syntax error"),
    ]
    with patch("sonny.isolated_syntax_executor.subprocess.run", side_effect=outcomes) as run:
        result = run_paired_syntax_checks(str(base), str(candidate), IMAGE)
    assert run.call_count == 2
    assert result["review"]["regression"] is True
    assert result["review"]["baseline_passed"] is True
    assert result["review"]["candidate_passed"] is False
    assert result["commit_allowed"] is False
    assert result["independently_verified"] is False
    assert result["baseline"]["command_sha256"] == result["candidate"]["command_sha256"]


def test_identical_snapshots_rejected_before_execution(tmp_path):
    base, candidate = workspaces(tmp_path)
    (candidate / "sonny" / "example.py").write_text("value = 1\n")
    with patch("sonny.isolated_syntax_executor.subprocess.run") as run:
        with pytest.raises(ValueError, match="differ"):
            run_paired_syntax_checks(str(base), str(candidate), IMAGE)
        run.assert_not_called()


def test_same_workspace_rejected(tmp_path):
    base, _ = workspaces(tmp_path)
    with pytest.raises(ValueError, match="separate"):
        run_paired_syntax_checks(str(base), str(base), IMAGE)


def test_second_run_failure_does_not_return_partial_evidence(tmp_path):
    base, candidate = workspaces(tmp_path)
    with patch("sonny.isolated_syntax_executor.subprocess.run", side_effect=[
        subprocess.CompletedProcess([], 0, b"", b""),
        FileNotFoundError(),
    ]):
        with pytest.raises(RuntimeError, match="unavailable"):
            run_paired_syntax_checks(str(base), str(candidate), IMAGE)
