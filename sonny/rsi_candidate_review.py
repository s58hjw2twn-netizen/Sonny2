"""Read-only combination of staged code checks and preregistered RSI evidence.

Caller-supplied scores and booleans are not independent verification.
This function never executes candidate code or authorizes a commit.
"""
from .candidate_evaluator import evaluate_candidate
from .rsi_evidence_gate import assess_experiment
from .paired_execution_review import summarize_pair


def review_candidate_experiment(staged, baseline_checks, candidate_checks,
                                manifest, baseline_scores, candidate_scores):
    """Require both checks and benchmark thresholds; fail closed."""
    code = evaluate_candidate(staged, baseline_checks, candidate_checks)
    evidence = assess_experiment(manifest, baseline_scores, candidate_scores)
    eligible = bool(code["passed"] and evidence["meets_preregistered_thresholds"])
    return {
        "task_id": code["task_id"],
        "candidate_sha256": code["candidate_sha256"],
        "code_checks_passed": code["passed"],
        "benchmark_thresholds_met": evidence["meets_preregistered_thresholds"],
        "manifest_sha256": evidence["manifest_sha256"],
        "fixture_sha256": evidence["fixture_sha256"],
        "regressions": code["regressions"],
        "benchmark_regressions": evidence["regressions"],
        "eligible_for_independent_replication": eligible,
        "independently_verified": False,
        "commit_allowed": False,
        "promotion_allowed": False,
        "status": "AWAITING_INDEPENDENT_REPLICATION" if eligible else "REJECTED_BY_COMBINED_GATE",
    }


def review_replication_records(review: dict, baseline_record: dict,
                               candidate_record: dict) -> dict:
    """Cross-check reported execution hashes; never authenticate caller records."""
    if not isinstance(review, dict) or review.get("eligible_for_independent_replication") is not True:
        raise ValueError("candidate has not passed preliminary evidence review")
    expected = review.get("candidate_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("candidate digest missing")
    paired = summarize_pair(baseline_record, candidate_record)
    if paired["candidate_snapshot_sha256"] != expected:
        raise ValueError("execution record does not match staged candidate")
    acceptable = paired["baseline_passed"] and paired["candidate_passed"] and not paired["regression"]
    return {
        "candidate_sha256": expected,
        "execution_records_consistent": acceptable,
        "evidence_authenticated": False,
        "independently_verified": False,
        "commit_allowed": False,
        "promotion_allowed": False,
        "status": "AWAITING_AUTHENTICATED_REPLICATION" if acceptable else "REJECTED_BY_REPLICATION_REVIEW",
    }
