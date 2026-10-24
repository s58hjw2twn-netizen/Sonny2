"""Run the same bounded syntax check on two separate source snapshots.

This is diagnostic orchestration, not independent verification or commit approval.
"""
from pathlib import Path

from sonny.isolated_syntax_executor import execute_syntax_check, fingerprint_workspace
from sonny.paired_execution_review import summarize_pair

_EVIDENCE_KEYS = ("snapshot_sha256", "command_sha256", "exit_code", "stdout_sha256", "stderr_sha256")


def run_paired_syntax_checks(baseline_workspace: str, candidate_workspace: str, image: str) -> dict:
    baseline = Path(baseline_workspace).resolve(strict=True)
    candidate = Path(candidate_workspace).resolve(strict=True)
    if baseline == candidate or baseline in candidate.parents or candidate in baseline.parents:
        raise ValueError("baseline and candidate must be separate, non-nested workspaces")
    baseline_hash = fingerprint_workspace(str(baseline))
    candidate_hash = fingerprint_workspace(str(candidate))
    if baseline_hash == candidate_hash:
        raise ValueError("candidate snapshot must differ from baseline")
    first = execute_syntax_check(str(baseline), image, baseline_hash)
    second = execute_syntax_check(str(candidate), image, candidate_hash)
    if first["snapshot_sha256"] != baseline_hash or second["snapshot_sha256"] != candidate_hash:
        raise RuntimeError("executor returned mismatched snapshot evidence")
    review = summarize_pair(
        {key: first[key] for key in _EVIDENCE_KEYS},
        {key: second[key] for key in _EVIDENCE_KEYS},
    )
    return {
        "baseline": first,
        "candidate": second,
        "review": review,
        "independently_verified": False,
        "commit_allowed": False,
    }
