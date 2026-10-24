import hashlib
import subprocess
from unittest.mock import patch

import pytest

from sonny.isolated_syntax_executor import execute_syntax_check

IMAGE = "python:3.11-slim@sha256:" + "a" * 64
SNAPSHOT = "b" * 64


def test_successful_execution_records_digests(tmp_path):
    result = subprocess.CompletedProcess([], 0, b"ok", b"")
    with patch("sonny.isolated_syntax_executor.subprocess.run", return_value=result) as run:
        evidence = execute_syntax_check(str(tmp_path), IMAGE, SNAPSHOT)
    assert run.call_args.kwargs["timeout"] == 30
    assert evidence["exit_code"] == 0
    assert evidence["stdout_sha256"] == hashlib.sha256(b"ok").hexdigest()
    assert evidence["commit_allowed"] is False
    assert evidence["evidence_authenticated"] is False


def test_failure_is_not_converted_to_success(tmp_path):
    with patch("sonny.isolated_syntax_executor.subprocess.run",
               return_value=subprocess.CompletedProcess([], 2, b"", b"bad")):
        evidence = execute_syntax_check(str(tmp_path), IMAGE, SNAPSHOT)
    assert evidence["exit_code"] == 2


def test_timeout_is_failure(tmp_path):
    with patch("sonny.isolated_syntax_executor.subprocess.run",
               side_effect=subprocess.TimeoutExpired(["docker"], 30)):
        evidence = execute_syntax_check(str(tmp_path), IMAGE, SNAPSHOT)
    assert evidence["exit_code"] == 124


def test_missing_docker_fails_closed(tmp_path):
    with patch("sonny.isolated_syntax_executor.subprocess.run",
               side_effect=FileNotFoundError()):
        with pytest.raises(RuntimeError):
            execute_syntax_check(str(tmp_path), IMAGE, SNAPSHOT)


def test_bad_snapshot_fingerprint_rejected(tmp_path):
    with pytest.raises(ValueError):
        execute_syntax_check(str(tmp_path), IMAGE, "not-a-hash")
