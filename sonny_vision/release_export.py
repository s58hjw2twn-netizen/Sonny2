"""Fail-closed release export with descriptor-based source validation.

Caller must independently establish reviewer authorization, image quality and
identity review. This module only verifies the signed exact-byte decision.
"""
from __future__ import annotations
import os
import stat
from pathlib import Path
from .review_gate_v17 import ReviewDecision, authorize_customer_release


def _read_regular_nofollow(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError("Source must be a regular file")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            return handle.read()
    finally:
        os.close(fd)


def export_reviewed(source_path: str, candidate_path: str, destination_path: str,
                    decision: ReviewDecision | None, secret: bytes,
                    quality_passed: bool, identity_reviewed: bool) -> bool:
    source, candidate, destination = map(Path, (source_path, candidate_path, destination_path))
    if source.is_symlink() or candidate.is_symlink() or destination.is_symlink():
        raise ValueError("Symlinks are not allowed")
    if destination.resolve() in {source.resolve(), candidate.resolve()}:
        raise ValueError("Destination must be distinct from source and candidate")
    if destination.exists():
        raise FileExistsError("Destination already exists")
    original = _read_regular_nofollow(source)
    restored = _read_regular_nofollow(candidate)
    if not authorize_customer_release(decision, original, restored, secret,
                                      quality_passed, identity_reviewed):
        return False
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(restored)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return True
