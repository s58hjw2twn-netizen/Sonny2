"""Bounded, offline patch applicability check in disposable Git workspaces.

Does not execute candidate code, run Docker, access test suites or promote.
"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

from .generator import generate_proposals
from .policy import validate_patch


def _git(*args, timeout=15):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=False, timeout=timeout)


def check_generated(source, *, max_candidates=3):
    root = Path(source).resolve(strict=True)
    if not root.is_dir() or not (root / ".git").exists():
        raise ValueError("Source must be a Git checkout")
    status = _git("-C", str(root), "status", "--porcelain", "-z")
    if status.returncode or status.stdout:
        raise ValueError("A clean Git checkout is required")
    revision = _git("-C", str(root), "rev-parse", "--verify", "HEAD^{commit}")
    if revision.returncode or len(revision.stdout.strip()) != 40:
        raise ValueError("Cannot resolve immutable revision")
    proposals = generate_proposals(root, max_candidates=max_candidates)
    results = []
    for proposal in proposals:
        patch = proposal["patch_text"]
        paths = validate_patch(patch)
        with tempfile.TemporaryDirectory(prefix="sonny-apl-patchcheck-") as tmp:
            workspace = Path(tmp) / "candidate"
            clone = _git("clone", "--no-hardlinks", "--no-checkout", "--",
                         str(root), str(workspace), timeout=30)
            if clone.returncode:
                raise RuntimeError("Disposable clone failed")
            checkout = _git("-C", str(workspace), "checkout", "--detach",
                            revision.stdout.strip())
            if checkout.returncode:
                raise RuntimeError("Disposable checkout failed")
            patch_file = Path(tmp) / "candidate.diff"
            patch_file.write_text(patch, encoding="utf-8")
            checked = _git("-C", str(workspace), "apply", "--check", "--",
                           str(patch_file))
            if checked.returncode:
                raise ValueError("Generated patch does not apply")
            applied = _git("-C", str(workspace), "apply", "--", str(patch_file))
            if applied.returncode:
                raise ValueError("Generated patch failed to apply")
            changed = _git("-C", str(workspace), "diff", "--name-only", "--")
            if changed.returncode or sorted(changed.stdout.splitlines()) != sorted(paths):
                raise ValueError("Unexpected changed paths")
            results.append({
                "candidate_id": proposal["candidate_id"],
                "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                "base_revision": revision.stdout.strip(),
                "changed_paths": paths,
                "applicable_in_disposable_checkout": True,
                "candidate_code_executed": False,
                "promotion": "FORBIDDEN",
            })
    return results
