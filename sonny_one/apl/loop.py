"""Bounded offline intake loop. Proposals are supplied, never self-promoted.

Every candidate is evaluated against the same immutable baseline. Held-out
feedback is not supplied to a generator. This is not recursive self-improvement.
"""
import argparse
import json
import math
import tempfile
from pathlib import Path
from .runner import evaluate
from .policy import append_lineage, sha256_bytes, validate_patch


def run_queue(proposals, *, max_candidates=3, **evaluation_args):
    if type(max_candidates) is not int or not 1 <= max_candidates <= 10:
        raise ValueError("Candidate budget must be an integer in [1, 10]")
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= max_candidates:
        raise ValueError("Proposal count exceeds budget or is empty")
    # Validate the whole manifest before executing any candidate.
    prepared = []
    seen = set()
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {"patch", "predicted_pass"}:
            raise ValueError("Each proposal requires patch and predicted_pass only")
        prediction = proposal["predicted_pass"]
        if type(prediction) not in (int, float) or not math.isfinite(prediction) or not 0 <= prediction <= 1:
            raise ValueError("Prediction must be a finite probability")
        data = Path(proposal["patch"]).read_text(encoding="utf-8")
        validate_patch(data)
        digest = sha256_bytes(data.encode())
        if digest in seen:
            raise ValueError("Duplicate candidate")
        seen.add(digest)
        prepared.append((proposal, digest, data))
    results = []
    for proposal, digest, validated_text in prepared:
        # Never reopen mutable inbox bytes for candidate execution. Pass the exact
        # snapshot that was validated and preregistered, even if inbox changes.
        with tempfile.TemporaryDirectory(prefix="apl-proposal-") as directory:
            frozen = Path(directory) / "candidate.diff"
            frozen.write_text(validated_text, encoding="utf-8")
            append_lineage(Path(evaluation_args["ledger"]), {
                "event": "proposal_prediction", "candidate_id": digest,
                "base_revision": evaluation_args["revision"],
                "predicted_pass": proposal["predicted_pass"], "promotion": "FORBIDDEN"})
            report = evaluate(patch_file=str(frozen), **evaluation_args)
        if report["candidate_id"] != digest:
            raise ValueError("Evaluated proposal differs from preregistered proposal")
        results.append(report)
        # Infrastructure failures stop the batch; test failures do not.
        if report.get("error") or any(
            type(report.get(k, {}).get("exit_code")) is not int
            or report[k]["exit_code"] not in (0, 1)
            for k in ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout")
        ):
            break
    return {"attempted": len(results), "budget": max_candidates,
            "reports": results, "promotion": "FORBIDDEN",
            "improvement_proven": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=3)
    for name in ("source", "revision", "trusted", "heldout", "image", "ledger"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--timeout", type=int, default=90)
    args = vars(parser.parse_args())
    proposals = json.loads(args.pop("manifest").read_text())
    print(json.dumps(run_queue(proposals, **args), indent=2))


if __name__ == "__main__":
    main()
