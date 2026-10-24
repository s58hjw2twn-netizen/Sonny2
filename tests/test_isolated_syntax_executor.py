import hashlib
import subprocess
from unittest.mock import patch

import pytest

from sonny.isolated_syntax_executor import execute_syntax_check, fingerprint_workspace

IMAGE = "python:3.11-slim@sha256:" + "a" * 64


def snapshot(tmp_path):
    (tmp_path / "sonny").mkdir()
    (tmp_path / "sonny" / "sample.py").write_text("x = 1\n")
    return fingerprint_workspace(str(tmp_path))


def test_successful_execution_records_digests(tmp_path):
    result = subprocess.CompletedProcess([], 0, b"ok", b"")
    with patch("sonny.isolated_syntax_executor.subprocess.run", return_value=result) as run:
        evidence = execute_syntax_check(str(tmp_path), IMAGE, snapshot(tmp_path))
    assert run.call_args.kwargs["timeout"] == 30
    assert evidence["exit_code"] == 0
    assert evidence["stdout_sha256"] == hashlib.sha256(b"ok").hexdigest()
    assert evidence["commit_allowed"] is False
    assert evidence["evidence_authenticated"] is False


def test_failure_is_not_converted_to_success(tmp_path):
    with patch("sonny.isolated_syntax_executor.subprocess.run",
               return_value=subprocess.CompletedProcess([], 2, b"", b"bad")):
        evidence = execute_syntax_check(str(tmp_path), IMAGE, snapshot(tmp_path))
    assert evidence["exit_code"] == 2


def test_timeout_is_failure(tmp_path):
    with patch("sonny.isolated_syntax_executor.subprocess.run",
               side_effect=subprocess.TimeoutExpired(["docker"], 30)):
        evidence = execute_syntax_check(str(tmp_path), IMAGE, snapshot(tmp_path))
    assert evidence["exit_code"] == 124


def test_missing_docker_fails_closed(tmp_path):
    with patch("sonny.isolated_syntax_executor.subprocess.run",
               side_effect=FileNotFoundError()):
        with pytest.raises(RuntimeError):
            execute_syntax_check(str(tmp_path), IMAGE, snapshot(tmp_path))


def test_bad_snapshot_fingerprint_rejected(tmp_path):
    with pytest.raises(ValueError):
        execute_syntax_check(str(tmp_path), IMAGE, "not-a-hash")


def test_workspace_mismatch_rejected_before_docker(tmp_path):
    (tmp_path / "sonny").mkdir()
    (tmp_path / "sonny" / "sample.py").write_text("x = 1\\n")
    with patch("sonny.isolated_syntax_executor.subprocess.run") as run:
        with pytest.raises(ValueError, match="fingerprint mismatch"):
            execute_syntax_check(str(tmp_path), IMAGE, "b" * 64)
        run.assert_not_called()


def test_symlink_rejected(tmp_path):
    (tmp_path / "sonny").mkdir()
    target = tmp_path / "outside.py"
    target.write_text("x = 1\\n")
    (tmp_path / "sonny" / "link.py").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        fingerprint_workspace(str(tmp_path))


def test_workspace_mutation_during_execution_rejected(tmp_path):
    original = snapshot(tmp_path)

    def mutate(*args, **kwargs):
        (tmp_path / "sonny" / "sample.py").write_text("x = 999\\n")
        return subprocess.CompletedProcess([], 0, b"success", b"")

    with patch("sonny.isolated_syntax_executor.subprocess.run", side_effect=mutate):
        with pytest.raises(RuntimeError, match="workspace changed"):
            execute_syntax_check(str(tmp_path), IMAGE, original)
