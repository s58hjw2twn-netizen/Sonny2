"""Read-only verification of an APL offline proposal bundle.

No candidate code, Docker, test suite or Git command is executed here.
"""
import hashlib
import json

from .policy import validate_patch


def inspect_bundle(bundle, *, max_candidates=3):
    if type(max_candidates) is not int or not 1 <= max_candidates <= 3:
        raise ValueError("Invalid candidate budget")
    if not isinstance(bundle, dict) or set(bundle) != {
        "format", "proposals", "sandbox_execution_approved",
        "ready_for_runner", "promotion", "note"
    }:
        raise ValueError("Invalid bundle schema")
    if (bundle["format"] != "apl-offline-proposal-bundle-v1"
            or bundle["sandbox_execution_approved"] is not False
            or bundle["ready_for_runner"] is not False
            or bundle["promotion"] != "FORBIDDEN"):
        raise ValueError("Unsafe bundle state")
    proposals = bundle["proposals"]
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= max_candidates:
        raise ValueError("Invalid proposal count")
    seen = set()
    revision = None
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {
            "candidate_id", "base_revision", "patch_sha256", "patch_text",
            "changed_paths", "applicable_in_disposable_checkout",
            "predicted_pass", "candidate_code_executed", "promotion"
        }:
            raise ValueError("Invalid proposal schema")
        patch = proposal["patch_text"]
        if not isinstance(patch, str):
            raise ValueError("Invalid patch")
        digest = hashlib.sha256(patch.encode("utf-8")).hexdigest()
        if (proposal["candidate_id"] != digest
                or proposal["patch_sha256"] != digest or digest in seen):
            raise ValueError("Invalid or repeated candidate identity")
        seen.add(digest)
        paths = validate_patch(patch)
        if proposal["changed_paths"] != paths:
            raise ValueError("Changed path mismatch")
        base = proposal["base_revision"]
        if (not isinstance(base, str) or len(base) != 40
                or any(ch not in "0123456789abcdef" for ch in base)):
            raise ValueError("Invalid base revision")
        if revision is None:
            revision = base
        elif revision != base:
            raise ValueError("Mixed base revisions")
        if (proposal["applicable_in_disposable_checkout"] is not True
                or proposal["predicted_pass"] is not None
                or proposal["candidate_code_executed"] is not False
                or proposal["promotion"] != "FORBIDDEN"):
            raise ValueError("Unsafe proposal state")
    return {
        "format": "apl-offline-dryrun-v1",
        "proposal_count": len(proposals),
        "base_revision": revision,
        "candidate_ids": sorted(seen),
        "bundle_sha256": hashlib.sha256(json.dumps(
            bundle, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("utf-8")).hexdigest(),
        "schema_and_hashes_valid": True,
        "git_applicability_rechecked": False,
        "candidate_code_executed": False,
        "sandbox_execution_approved": False,
        "promotion": "FORBIDDEN",
        "limitations": "Untrusted applicability claims are not reverified; "
                       "requires independent checkout and sandbox validation.",
    }
