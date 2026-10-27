"""Offline evaluator-side attestation builder for a separately trusted service.

This is a pure data constructor, not a server and not a signer. The real
service must independently run tests, protect fixtures, and sign canonical
payload bytes with its own protected Ed25519 private key.
"""
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def build_unsigned_attestation(request, *, evaluator_id, suite_result):
    if not isinstance(request, dict) or set(request) != {
            "candidate_sha256", "base_revision", "suite_sha256"}:
        raise ValueError("Invalid evaluation request")
    if not isinstance(request["candidate_sha256"], str) or not _SHA.fullmatch(request["candidate_sha256"]):
        raise ValueError("Invalid candidate digest")
    if not isinstance(request["base_revision"], str) or not _REV.fullmatch(request["base_revision"]):
        raise ValueError("Invalid base revision")
    if not isinstance(request["suite_sha256"], str) or not _SHA.fullmatch(request["suite_sha256"]):
        raise ValueError("Invalid suite digest")
    if not isinstance(evaluator_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", evaluator_id):
        raise ValueError("Invalid evaluator identity")
    if suite_result not in ("PASS", "FAIL", "ERROR"):
        raise ValueError("Invalid suite result")
    return {"schema_version": 1,
            "candidate_sha256": request["candidate_sha256"],
            "base_revision": request["base_revision"],
            "suite_sha256": request["suite_sha256"],
            "evaluator_id": evaluator_id,
            "result": suite_result,
            "signature": "",
            "signed": False,
            "execution_performed": False,
            "confidentiality_verified": False,
            "promotion": "FORBIDDEN"}
