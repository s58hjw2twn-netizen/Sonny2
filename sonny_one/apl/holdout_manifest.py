"""Canonical, bounded evaluation request for separately operated holdout labs.

A trusted controller creates this request before sending a candidate to an
external evaluator. It contains no private test content or signing material.
"""
import hashlib
import json
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def create_holdout_request(candidate_bytes, *, base_revision, suite_sha256):
    if not isinstance(candidate_bytes, bytes) or not candidate_bytes:
        raise ValueError("Nonempty candidate bytes required")
    if len(candidate_bytes) > 2 * 1024 * 1024:
        raise ValueError("Candidate exceeds evaluation intake limit")
    if not isinstance(base_revision, str) or not _REV.fullmatch(base_revision):
        raise ValueError("Invalid base revision")
    if not isinstance(suite_sha256, str) or not _SHA.fullmatch(suite_sha256):
        raise ValueError("Invalid trusted suite digest")
    return {"candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
            "base_revision": base_revision, "suite_sha256": suite_sha256}


def canonical_request_sha256(request):
    if not isinstance(request, dict) or set(request) != {
            "candidate_sha256", "base_revision", "suite_sha256"}:
        raise ValueError("Invalid evaluation request fields")
    if not isinstance(request["candidate_sha256"], str) or not _SHA.fullmatch(request["candidate_sha256"]):
        raise ValueError("Invalid candidate digest")
    if not isinstance(request["base_revision"], str) or not _REV.fullmatch(request["base_revision"]):
        raise ValueError("Invalid revision")
    if not isinstance(request["suite_sha256"], str) or not _SHA.fullmatch(request["suite_sha256"]):
        raise ValueError("Invalid suite digest")
    return hashlib.sha256(json.dumps(
        request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
