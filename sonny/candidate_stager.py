"""Deterministic, in-memory candidate patch validation for Sonny ONE.

No filesystem, shell, network, git, model or deployment side effects.
A later isolated executor must independently enforce these boundaries.
"""
import hashlib
from dataclasses import dataclass

from .research_agent import Task, validate_task

MAX_FILE_BYTES = 200_000
MAX_PATCH_BYTES = 32_000


@dataclass(frozen=True)
class Replacement:
    path: str
    before: str
    after: str


def stage_candidate(task: Task, files: dict[str, str], changes: list[Replacement]) -> dict:
    validate_task(task)
    if task.risk != "low":
        raise ValueError("only low-risk tasks may be staged")
    if not changes or len(changes) > 8:
        raise ValueError("invalid change count")
    allowed = set(task.paths)
    # Validate the complete snapshot, not just the paths being patched.
    # Reject unsafe keys and oversized or non-text inputs before fingerprinting.
    if not isinstance(files, dict) or not files or len(files) > 128:
        raise ValueError("invalid snapshot count")
    total_snapshot_bytes = 0
    for path, content in files.items():
        if not isinstance(path, str) or not path.startswith(("sonny/", "tests/", "docs/")):
            raise ValueError("snapshot path outside allowed roots")
        validate_task(Task(task.task_id, task.objective, (path,), task.risk))
        if not isinstance(content, str) or len(content.encode()) > MAX_FILE_BYTES:
            raise ValueError("invalid snapshot file")
        total_snapshot_bytes += len(content.encode())
        if total_snapshot_bytes > 2_000_000:
            raise ValueError("snapshot exceeds total size limit")
    staged = dict(files)
    touched = set()
    total = 0
    for change in changes:
        if change.path not in allowed:
            raise ValueError("patch path outside task scope")
        if change.path in touched:
            raise ValueError("only one replacement per file per batch")
        touched.add(change.path)
        if change.path not in files:
            raise ValueError("file must already exist")
        original = files[change.path]
        if not isinstance(original, str) or not isinstance(change.before, str) or not isinstance(change.after, str):
            raise ValueError("only text files supported")
        if not change.before or original.count(change.before) != 1:
            raise ValueError("replacement anchor must occur exactly once")
        total += len(change.before.encode()) + len(change.after.encode())
        if total > MAX_PATCH_BYTES:
            raise ValueError("patch exceeds size limit")
        candidate = original.replace(change.before, change.after, 1)
        if len(candidate.encode()) > MAX_FILE_BYTES:
            raise ValueError("candidate exceeds file size limit")
        staged[change.path] = candidate
    digest = hashlib.sha256()
    for path in sorted(staged):
        digest.update(path.encode() + bytes([0]))
        digest.update(staged[path].encode() + bytes([0]))
    return {
        "task_id": task.task_id,
        "candidate": staged,
        "sha256": digest.hexdigest(),
        "changed_paths": sorted(touched),
        "writes_performed": 0,
        "execution_allowed": False,
        "status": "STAGED_FOR_INDEPENDENT_TESTING",
    }
