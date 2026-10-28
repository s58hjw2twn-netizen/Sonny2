"""Read-only verifier for a model-generated research patch.

This checks that the proposal matches the current source and reconstructs the
candidate without executing or committing untrusted code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from sonny_one.development_controller.coding_context import build_coding_context
from sonny_one.development_controller.proposal_static_gate import evaluate_static_proposal


def verify_proposal(path: Path, repo_root: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != "sonny-one-review-only-model-proposal-v1":
        raise ValueError("unsupported proposal artifact")
    if data.get("approved_for_execution") is not False or data.get("commit_created") is not False:
        raise ValueError("proposal must be review-only")
    proposal = data.get("proposal")
    if not isinstance(proposal, dict) or not isinstance(proposal.get("patch_text"), str):
        raise ValueError("missing proposed patch")
    if proposal.get("task_id") != "RES-001":
        raise ValueError("unexpected task")
    context = build_coding_context(repo_root)
    if data.get("baseline_sha256") != context["source_sha256"]:
        raise ValueError("stale baseline fingerprint")
    checked = evaluate_static_proposal(context["source"], proposal["patch_text"])
    if checked != data.get("static_evaluation"):
        raise ValueError("static evaluation mismatch")
    return {"verified": True, "executed": False, "committed": False,
            "patch_sha256": hashlib.sha256(proposal["patch_text"].encode()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(verify_proposal(args.proposal, args.repo_root), sort_keys=True))


if __name__ == "__main__":
    main()
