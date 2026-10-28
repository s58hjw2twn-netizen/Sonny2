"""Evaluator response contract: validate signed-result envelope, never execute it.

Actual Ed25519 verification is delegated to the existing trusted review layer.
This protocol checks required fields and request binding only.
"""
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def validate_evaluator_response(request, response):
    if not isinstance(request, dict) or set(request) != {
            "candidate_sha256", "base_revision", "suite_sha256"}:
        raise ValueError("Invalid originating request")
    if not isinstance(response, dict) or set(response) != {
            "candidate_sha256", "base_revision", "suite_sha256",
            "evaluator_id", "result", "signature", "schema_version"}:
        raise ValueError("Invalid evaluator response fields")
    for key in ("candidate_sha256", "suite_sha256"):
        if not isinstance(request[key], str) or not _SHA.fullmatch(request[key]):
            raise ValueError("Invalid request digest")
        if response[key] != request[key]:
            raise ValueError("Response does not match originating request")
    if not isinstance(request["base_revision"], str) or not _REV.fullmatch(request["base_revision"]):
        raise ValueError("Invalid request revision")
    if response["base_revision"] != request["base_revision"]:
        raise ValueError("Response revision mismatch")
    if not isinstance(response["evaluator_id"], str) or not response["evaluator_id"]:
        raise ValueError("Missing evaluator identity")
    if response["result"] not in ("PASS", "FAIL", "ERROR"):
        raise ValueError("Invalid evaluator result")
    if response["schema_version"] != 1:
        raise ValueError("Unsupported evaluator response schema")
    if not isinstance(response["signature"], str) or not response["signature"]:
        raise ValueError("Missing evaluator signature")
    return {"response_matches_request": True, "signature_verified": False,
            "confidentiality_verified": False, "independent_custody_verified": False,
            "promotion": "FORBIDDEN", "result_untrusted": response["result"]}
