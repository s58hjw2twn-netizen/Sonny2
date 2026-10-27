"""Release reviewed restorations only after exact-byte signed authorization.

The source and candidate must be regular files, not symlinks. The output is
created exclusively and never overwrites a previous delivery. This module
does not itself establish that the reviewer is an authorized operator.
"""
from __future__ import annotations
import os
from pathlib import Path
from .review_gate_v17 import ReviewDecision, authorize_customer_release


def export_reviewed(source_path: str, candidate_path: str, destination_path: str,
                    decision: ReviewDecision | None, secret: bytes,
                    quality_passed: bool, identity_reviewed: bool) -> bool:
    source, candidate, destination = map(Path, (source_path, candidate_path, destination_path))
    if source.is_symlink() or candidate.is_symlink() or destination.is_symlink():
        raise ValueError("Symlinks are not allowed")
    if not source.is_file() or not candidate.is_file():
        raise ValueError("Source and candidate must exist")
    if destination.resolve() in {source.resolve(), candidate.resolve()}:
        raise ValueError("Destination must be distinct from source and candidate")
    if destination.exists():
        raise FileExistsError("Destination already exists")
    original = source.read_bytes()
    restored = candidate.read_bytes()
    if not authorize_customer_release(decision, original, restored, secret,
                                      quality_passed, identity_reviewed):
        return False
    # O_EXCL prevents overwriting an existing export or following an existing symlink.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(restored)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return True
