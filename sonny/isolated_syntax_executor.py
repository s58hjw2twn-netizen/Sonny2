"""Bounded Docker execution of static syntax checks; no commit authority.

Run only in a trusted worker with Docker installed and no secrets mounted.
This is not a general-purpose untrusted-code sandbox.
"""
import hashlib
import json
import subprocess

from sonny.isolated_test_command import build_test_command


def execute_syntax_check(workspace: str, image: str, snapshot_sha256: str) -> dict:
    if not isinstance(snapshot_sha256, str) or len(snapshot_sha256) != 64 or any(
        c not in "0123456789abcdef" for c in snapshot_sha256
    ):
        raise ValueError("invalid snapshot fingerprint")
    command = build_test_command(workspace, image)
    command_hash = hashlib.sha256(
        json.dumps(command[command.index(image):], separators=(",", ":")).encode()
    ).hexdigest()
    try:
        result = subprocess.run(
            command, capture_output=True, timeout=30, check=False,
            stdin=subprocess.DEVNULL,
        )
        code = result.returncode
        stdout = result.stdout[:1048576]
        stderr = result.stderr[:1048576]
    except subprocess.TimeoutExpired:
        code = 124
        stdout = b""
        stderr = b"execution timed out"
    except OSError as exc:
        raise RuntimeError("Docker executor unavailable") from exc
    if code < 0:
        code = 128 + abs(code)
    if code > 255:
        code = 255
    return {
        "snapshot_sha256": snapshot_sha256,
        "command_sha256": command_hash,
        "exit_code": code,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "evidence_authenticated": False,
        "commit_allowed": False,
    }
