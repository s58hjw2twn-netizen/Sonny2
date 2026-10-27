"""Protocol contract for a separately deployed APL holdout evaluator.

This module validates requests only. It intentionally does not execute
candidate code, load private fixtures, or sign results. Those operations belong
in a separately provisioned evaluator service with independent key custody.
"""
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def validate_external_evaluator_request(request):
    if not isinstance(request, dict) or set(request) != {
            "candidate_sha256", "base_revision", "suite_sha256"}:
        raise ValueError("Invalid evaluator request fields")
    if not isinstance(request["candidate_sha256"], str) or not _SHA.fullmatch(request["candidate_sha256"]):
        raise ValueError("Invalid candidate digest")
    if not isinstance(request["base_revision"], str) or not _REV.fullmatch(request["base_revision"]):
        raise ValueError("Invalid base revision")
    if not isinstance(request["suite_sha256"], str) or not _SHA.fullmatch(request["suite_sha256"]):
        raise ValueError("Invalid suite digest")
    return {"candidate_sha256": request["candidate_sha256"],
            "base_revision": request["base_revision"],
            "suite_sha256": request["suite_sha256"],
            "execution_authorized": False,
            "signature_authorized": False,
            "confidentiality_verified": False,
            "promotion": "FORBIDDEN"}
