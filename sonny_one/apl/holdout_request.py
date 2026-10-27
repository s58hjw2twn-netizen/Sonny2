"""Cross-check signed external evidence against a trusted local evaluation request.

The request is prepared by the trusted controller before external evaluation.
Candidate-supplied metadata and attestation-supplied keys are never accepted
as authoritative. A signed PASS still cannot authorize promotion.
"""
import re
from .external_review import review_external_holdout

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def review_pinned_holdout_request(request, attestation, *,
                                  trusted_evaluator_id,
                                  trusted_public_key_pem,
                                  trusted_public_key_sha256):
    if not isinstance(request, dict) or set(request) != {
            "candidate_sha256", "base_revision", "suite_sha256"}:
        raise ValueError("Invalid trusted evaluation request")
    candidate = request["candidate_sha256"]
    revision = request["base_revision"]
    suite = request["suite_sha256"]
    if not isinstance(candidate, str) or not _SHA.fullmatch(candidate):
        raise ValueError("Invalid trusted candidate digest")
    if not isinstance(revision, str) or not _REV.fullmatch(revision):
        raise ValueError("Invalid trusted base revision")
    if not isinstance(suite, str) or not _SHA.fullmatch(suite):
        raise ValueError("Invalid trusted suite digest")
    if not isinstance(attestation, dict) or attestation.get("suite_sha256") != suite:
        raise ValueError("Evaluator suite digest differs from trusted request")
    result = review_external_holdout(
        attestation, candidate_sha256=candidate,
        base_revision=revision, trusted_evaluator_id=trusted_evaluator_id,
        trusted_public_key_pem=trusted_public_key_pem,
        trusted_public_key_sha256=trusted_public_key_sha256)
    return {**result, "suite_sha256": suite,
            "trusted_request_binding_verified": True,
            "promotion": "FORBIDDEN", "improvement_proven": False}
