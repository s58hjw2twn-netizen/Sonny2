"""Constrained Docker command builder for independent test workers.

Builds arguments only; it never starts a container or authorizes a commit.
The caller must provision a disposable, verified workspace outside this module.
"""
from pathlib import Path


def build_test_command(workspace: str, image: str) -> list[str]:
    root = Path(workspace)
    if any(c in str(root) for c in (",", "\\n", "\\r")):\n        raise ValueError("workspace path contains unsupported mount characters")\n    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("workspace must be an existing absolute non-symlink directory")
    if not image.startswith("python:3.11-slim@sha256:"):
        raise ValueError("container image must be a pinned Python digest")
    digest = image.partition("@sha256:")[2]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid image digest")
    return [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "64", "--memory", "256m", "--cpus", "1",
        "--user", "65534:65534",
        "--tmpfs", "/tmp:rw,nosuid,noexec,size=16m",
        "--mount", f"type=bind,source={root},target=/workspace,readonly",
        "--workdir", "/workspace", image,
        "python", "-m", "unittest", "discover", "-s", "tests",
    ]
