"""Deterministic offline candidate proposal generation for APL-001.

Produces reviewable patch *text* from a fixed allowlisted edit recipe. It does
not apply patches, call a model, inspect holdouts, or select a winner.
"""
import difflib
import hashlib
import math
from pathlib import Path

from .policy import validate_patch


_ALLOWED_TARGET = "sonny_one/apl_targets/offline_strategy.py"


def generate_proposals(source, *, target=_ALLOWED_TARGET, max_candidates=3):
    """Create bounded diffs for known safe text substitutions.

    This is a deterministic engineering baseline, not an autonomous AI.
    """
    if type(max_candidates) is not int or not 1 <= max_candidates <= 3:
        raise ValueError("Candidate budget must be an integer in [1, 3]")
    if target != _ALLOWED_TARGET:
        raise ValueError("Generator target is not allowlisted")
    root = Path(source).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Source must be a directory")
    path = root / target
    if path.is_symlink() or not path.is_file() or path.resolve() != path:
        raise ValueError("Unsafe or missing target")
    original = path.read_text(encoding="utf-8")
    if len(original.encode("utf-8")) > 65536:
        raise ValueError("Target exceeds size budget")
    if not original.endswith("\n"):
        raise ValueError("Target must end with newline")
    recipes = (
        ("return sum(values) / len(values)", "return sum(values) / len(values) if values else 0.0"),
        ("return sorted(values)[0]", "return min(values) if values else None"),
        ("return max(values)", "return max(values) if values else None"),
    )
    results = []
    for before, after in recipes:
        if original.count(before) != 1 or after in original:
            continue
        modified = original.replace(before, after, 1)
        diff = "".join(difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="a/" + target, tofile="b/" + target,
        ))
        # Standard Git unified-diff headers required by the existing policy.
        diff = "diff --git a/{0} b/{0}\n--- a/{0}\n+++ b/{0}\n".format(target) + "".join(
            diff.splitlines(keepends=True)[2:]
        )
        validate_patch(diff)
        results.append({
            "candidate_id": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
            "patch_text": diff,
            "recipe": before,
            "predicted_pass": None,
            "promotion": "FORBIDDEN",
        })
        if len(results) >= max_candidates:
            break
    return results
