"""Prepare offline, reviewable APL proposal bundles without executing code.

The bundle is intentionally not a run_queue manifest: predicted pass
probabilities must be independently preregistered before any sandbox run.
"""
import hashlib
import json
from pathlib import Path

from .generator import generate_proposals
from .patchcheck import check_generated


def prepare_bundle(source, *, max_candidates=3):
    checked = check_generated(source, max_candidates=max_candidates)
    generated = generate_proposals(source, max_candidates=max_candidates)
    if len(checked) != len(generated):
        raise ValueError("Proposal verification count mismatch")
    proposals = []
    for expected, proposal in zip(checked, generated):
        digest = hashlib.sha256(proposal["patch_text"].encode("utf-8")).hexdigest()
        if (expected["candidate_id"] != digest
                or expected["patch_sha256"] != digest
                or expected["promotion"] != "FORBIDDEN"):
            raise ValueError("Proposal verification identity mismatch")
        proposals.append({
            "candidate_id": digest,
            "base_revision": expected["base_revision"],
            "patch_sha256": digest,
            "patch_text": proposal["patch_text"],
            "changed_paths": expected["changed_paths"],
            "applicable_in_disposable_checkout": True,
            "predicted_pass": None,
            "candidate_code_executed": False,
            "promotion": "FORBIDDEN",
        })
    if not proposals:
        raise ValueError("No allowlisted proposal recipes match source")
    return {
        "format": "apl-offline-proposal-bundle-v1",
        "proposals": proposals,
        "sandbox_execution_approved": False,
        "ready_for_runner": False,
        "promotion": "FORBIDDEN",
        "note": "No tests executed. Requires independently preregistered predictions, "
                "trusted sandbox and held-out custody before evaluation.",
    }


def write_bundle(bundle, destination):
    """Create new JSON artifact; never overwrite existing evidence."""
    path = Path(destination)
    if path.is_symlink():
        raise ValueError("Symlink output is prohibited")
    data = json.dumps(bundle, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if len(data.encode("utf-8")) > 500_000:
        raise ValueError("Bundle exceeds size limit")
    with path.open("x", encoding="utf-8") as handle:
        handle.write(data)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
