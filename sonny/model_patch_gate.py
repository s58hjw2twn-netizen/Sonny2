"""Validate model-proposed patches before any staging or execution.

The model is untrusted. This gate does not contact a model, write files,
run code, or authorize commits.
"""
import hashlib

MAX_PATCH_BYTES = 32_000
ALLOWED_PREFIXES = ("sonny/", "tests/")


def validate_model_patch(proposal: dict) -> dict:
    if not isinstance(proposal, dict) or set(proposal) != {"path", "content", "reason"}:
        raise ValueError("invalid model patch schema")
    path, content, reason = proposal["path"], proposal["content"], proposal["reason"]
    if not isinstance(path, str) or not path.startswith(ALLOWED_PREFIXES):
        raise ValueError("patch path not allowlisted")
    if (path.startswith("/") or "\\" in path or
            any(part in ("", ".", "..") for part in path.split("/")) or
            not path.endswith(".py") or path.startswith("tests/__")):
        raise ValueError("unsafe patch path")
    if not isinstance(content, str) or not isinstance(reason, str):
        raise ValueError("invalid patch fields")
    encoded = content.encode("utf-8")
    if not encoded or len(encoded) > MAX_PATCH_BYTES or "\x00" in content:
        raise ValueError("invalid patch size or content")
    if not reason.strip() or len(reason) > 500:
        raise ValueError("invalid patch rationale")
    return {
        "path": path,
        "content_sha256": hashlib.sha256(encoded).hexdigest(),
        "content_bytes": len(encoded),
        "approved_for_staging": False,
        "commit_allowed": False,
        "status": "MODEL_PATCH_VALIDATED_NOT_APPROVED",
    }


def validate_scoped_model_patch(proposal: dict, allowed_paths: tuple[str, ...]) -> dict:
    """Validate an untrusted proposal against an independently supplied task scope."""
    result = validate_model_patch(proposal)
    if not isinstance(allowed_paths, tuple) or not allowed_paths:
        raise ValueError("task scope required")
    if result["path"] not in allowed_paths:
        raise ValueError("proposal outside approved task scope")
    return result
