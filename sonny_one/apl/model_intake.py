"""Fail-closed intake of untrusted model-authored patch text.

This module does not call a model, apply patches, read holdouts, or promote code.
The caller must obtain proposals outside the trusted evaluation environment.
"""
import hashlib
import math
import re
import tempfile
from pathlib import Path

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
    if type(prediction) not in (int, float) or not math.isfinite(prediction) or not 0 <= prediction <= 1:
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


def evaluate_model_proposals(payloads, *, max_candidates=3, **evaluation_args):
    """Register all model patches before executing any in the bounded APL queue.

    Only experimental patch text enters disposable files. The declared model
    name is unverified; no credentials, holdouts, or model tools are exposed.
    """
    from .loop import run_queue
    from .policy import append_lineage

    if type(max_candidates) is not int or not 1 <= max_candidates <= 3:
        raise ValueError("Model candidate budget must be between 1 and 3")
    if not isinstance(payloads, list) or not 1 <= len(payloads) <= max_candidates:
        raise ValueError("Model proposal count exceeds budget or is empty")
    if not isinstance(evaluation_args.get("ledger"), (str, Path)):
        raise ValueError("Trusted lineage ledger required")
    records = [register_model_proposal(item, base_revision=evaluation_args["revision"])
               for item in payloads]
    if len({r["candidate_id"] for r in records}) != len(records):
        raise ValueError("Duplicate model patches prohibited")
    with tempfile.TemporaryDirectory(prefix="apl-model-intake-") as tmp:
        manifest = []
        for index, record in enumerate(records):
            patch = Path(tmp) / ("candidate-%d.diff" % index)
            patch.write_text(record["patch_text"], encoding="utf-8")
            manifest.append({"patch": str(patch), "predicted_pass": record["predicted_pass"]})
        for record in records:
            append_lineage(Path(evaluation_args["ledger"]), {
                "event": "unverified_model_proposal",
                "candidate_id": record["candidate_id"],
                "base_revision": record["base_revision"],
                "model_id_unverified": record["model_id_unverified"],
                "predicted_pass": record["predicted_pass"],
                "target_paths": record["target_paths"],
                "model_identity_authenticated": False,
                "promotion": "FORBIDDEN",
            })
        return run_queue(manifest, max_candidates=max_candidates, **evaluation_args)
