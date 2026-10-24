"""Bounded Docker execution of static syntax checks; no commit authority.

Run only in a trusted worker with Docker installed and no secrets mounted.
This is not a general-purpose untrusted-code sandbox.
"""
import hashlib
import json
import subprocess
from pathlib import Path

from sonny.isolated_test_command import build_test_command



def fingerprint_workspace(workspace: str) -> str:
    """Hash a bounded, symlink-free source snapshot using evaluator framing."""
    root = Path(workspace)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("invalid workspace")
    digest = hashlib.sha256()
    count = total = 0
    for folder in ("sonny", "tests"):
        base = root / folder
        if base.is_symlink():
            raise ValueError("symlinked source directory")
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                raise ValueError("symlinked workspace entry")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError("non-regular workspace entry")
            if path.suffix != ".py":
                raise ValueError("unexpected workspace file")
            count += 1
            if count > 128 or path.stat().st_size > 200000:
                raise ValueError("workspace limit exceeded")
            raw = path.read_bytes()
            total += len(raw)
            if total > 2000000:
                raise ValueError("workspace limit exceeded")
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode() + bytes([0]))
            digest.update(raw + bytes([0]))
    if count == 0:
        raise ValueError("empty workspace")
    return digest.hexdigest()

def execute_syntax_check(workspace: str, image: str, snapshot_sha256: str) -> dict:
    if not isinstance(snapshot_sha256, str) or len(snapshot_sha256) != 64 or any(
        c not in "0123456789abcdef" for c in snapshot_sha256
    ):
        raise ValueError("invalid snapshot fingerprint")
    command = build_test_command(workspace, image)
    if fingerprint_workspace(workspace) != snapshot_sha256:
        raise ValueError("workspace fingerprint mismatch")
    command_hash = hashlib.sha256(
        json.dumps(command[command.index(image):], separators=(",", ":")).encode()
    ).hexdigest()
    try:
        result = subprocess.run(
            command, capture_output=True, timeout=30, check=False,
            stdin=subprocess.DEVNULL,
        )
        code = result.returncode
        if len(result.stdout) > 1048576 or len(result.stderr) > 1048576:
            raise RuntimeError("executor output limit exceeded")
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        code = 124
        stdout = b""
        stderr = b"execution timed out"
    except OSError as exc:
        raise RuntimeError("Docker executor unavailable") from exc
    if fingerprint_workspace(workspace) != snapshot_sha256:
        raise RuntimeError("workspace changed during execution")
    if code in (125, 126, 127):
        raise RuntimeError("Docker failed to start or execute the container")
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
