"""APL-001 paired comparison of independently produced test reports.

This module does not execute code, select a winner, or authorize promotion.
It fails closed on incomplete results and keeps baseline and candidate scores separate.
"""
import json
from pathlib import Path


def compare(baseline: dict, candidate: dict) -> dict:
    for label, report in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(report, dict):
            raise ValueError(f"{label} must be a report object")
        for suite in ("deterministic", "heldout"):
            result = report.get(suite)
            if not isinstance(result, dict) or type(result.get("exit_code")) is not int:
                raise ValueError(f"{label} missing {suite} exit code")
        if not isinstance(report.get("base_revision"), str) or not report["base_revision"]:
            raise ValueError(f"{label} missing base revision")
    if baseline["base_revision"] != candidate["base_revision"]:
        raise ValueError("Mismatched base revisions")
    outcomes = {}
    for suite in ("deterministic", "heldout"):
        b = baseline[suite]["exit_code"] == 0
        c = candidate[suite]["exit_code"] == 0
        outcomes[suite] = {"baseline_pass": b, "candidate_pass": c,
                           "regression": b and not c, "repair": not b and c}
    return {"base_revision": baseline["base_revision"], "suites": outcomes,
            "review_required": True, "promotion": "FORBIDDEN",
            "improvement_proven": False,
            "note": "Suite exit codes alone cannot establish functional improvement."}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compare(json.loads(args.baseline.read_text()),
                             json.loads(args.candidate.read_text())), indent=2))


if __name__ == "__main__":
    main()
