"""One-shot, review-only local coding-model proposal CLI.

Requires an already installed Ollama model and a running loopback service.
Does not install software, execute generated code, commit, deploy, or alter
the task queue. Writes a new proposal JSON file only after APL patch policy
validation. Output paths must be user-chosen and must not exist.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sonny_one.development_controller.model_proposal_adapter import ModelProposalAdapter
from sonny_one.development_controller.ollama_proposal_producer import OllamaProposalProducer


def generate_review_proposal(*, model: str, output: Path,
                             enabled: bool = False) -> dict:
    if not enabled:
        raise PermissionError("explicit --allow-local-model flag required")
    if output.is_symlink() or output.exists():
        raise ValueError("output already exists or is a symlink")
    task = {"id": "RES-001", "track": "research",
            "title": "Offline research candidate proposal",
            "state": "ready", "priority": 1, "requires_approval": False}
    adapter = ModelProposalAdapter(
        OllamaProposalProducer(model=model, enabled=True))
    proposal = adapter.propose(task)
    report = {"format": "sonny-one-review-only-model-proposal-v1",
              "proposal": proposal, "approved_for_execution": False,
              "commit_created": False, "task_completed": False}
    serialized = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if len(serialized.encode("utf-8")) > 50000:
        raise ValueError("proposal artifact exceeds size limit")
    with output.open("x", encoding="utf-8") as stream:
        stream.write(serialized)
    return {"candidate_id": proposal["candidate_id"],
            "output": str(output), "review_only": True,
            "commit_created": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-local-model", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_review_proposal(
            model=args.model, output=args.output,
            enabled=args.allow_local_model)
    except (ValueError, PermissionError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
