"""Fail-closed intake of untrusted model-authored patch text.

This module does not call a model, apply patches, read holdouts, or promote code.
The caller must obtain proposals outside the trusted evaluation environment.
"""
import hashlib
import json
import re

from .policy import MAX_PATCH_BYTES, validate_patch

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")


def register_model_proposal(payload, *, base_revision):
    """Validate a model response and return a review-only immutable-text record.

    Payload fields are deliberately strict to avoid silently trusting model
    claims, paths, execution instructions, or fabricated test outcomes.
    """
    if not isinstance(payload, dict) or set(payload) != {
        "model_id", "patch_text", "predicted_pass"
    }:
        raise ValueError("Model proposal must contain only model_id, patch_text, predicted_pass")
    if not isinstance(base_revision, str) or not _REV.fullmatch(base_revision):
        raise ValueError("Full lowercase 40-character base revision required")
    model = payload["model_id"]
    if (not isinstance(model, str) or not 1 <= len(model) <= 128
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/@+-]*", model)):
        raise ValueError("Invalid model identifier")
    prediction = payload["predicted_pass"]
    if type(prediction) not in (int, float) or not 0 <= prediction <= 1:
        raise ValueError("Invalid predicted pass probability")
    patch = payload["patch_text"]
    if not isinstance(patch, str) or len(patch.encode("utf-8")) > MAX_PATCH_BYTES:
        raise ValueError("Invalid patch text or size")
    paths = validate_patch(patch)
    digest = hashlib.sha256(patch.encode("utf-8")).hexdigest()
    return {
        "candidate_id": digest,
        "base_revision": base_revision,
        "model_id_unverified": model,
        "predicted_pass": prediction,
        "target_paths": paths,
        "patch_text": patch,
        "patch_sha256": digest,
        "model_identity_authenticated": False,
        "tests_executed": False,
        "holdout_access_granted": False,
        "promotion": "FORBIDDEN",
        "improvement_proven": False,
    }
