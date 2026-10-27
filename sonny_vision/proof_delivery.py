"""Framework-neutral approval proof delivery; never exposes master paths.

The hosting service must authenticate the caller, provide a trusted customer_id,
use HTTPS, and keep the proof directory inaccessible to static-file serving.
"""
from __future__ import annotations
import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from .proof_access import verify_proof_token


@dataclass(frozen=True)
class ProofResponse:
    status: int
    body: bytes
    headers: dict[str, str]


_DENY_HEADERS = {
    "Cache-Control": "no-store, private",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; sandbox",
}


def serve_approval_proof(*, proof_path: str, job_id: str, customer_id: str,
                         authenticated_customer_id: str, token: str,
                         expected_proof_sha256: str, secret: bytes, now: int,
                         max_proof_bytes: int = 8_000_000) -> ProofResponse:
    denied = ProofResponse(403, b"Forbidden", dict(_DENY_HEADERS))
    if (not customer_id or not authenticated_customer_id
            or customer_id != authenticated_customer_id):
        return denied
    if not verify_proof_token(token, job_id, customer_id,
                              expected_proof_sha256, secret, now):
        return denied
    if not 1 <= max_proof_bytes <= 8_000_000:
        return denied
    path = Path(proof_path)
    if path.suffix.lower() not in {".jpg", ".jpeg"} or path.is_symlink():
        return denied
    fd = None
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= max_proof_bytes:
            return denied
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(max_proof_bytes + 1)
        if len(data) > max_proof_bytes:
            return denied
        if hashlib.sha256(data).hexdigest() != expected_proof_sha256:
            return denied
        if not data.startswith(b"\xff\xd8\xff"):
            return denied
        return ProofResponse(200, data, {**_DENY_HEADERS,
                                        "Content-Type": "image/jpeg",
                                        "Content-Disposition": "inline"})
    except (OSError, ValueError):
        return denied
    finally:
        if fd is not None:
            os.close(fd)
