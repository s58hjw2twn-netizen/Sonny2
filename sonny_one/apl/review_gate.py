"""Conservative, read-only RSI evidence gate for APL-001.

A statistically positive delta is not proof of RSI. This gate records whether
an experiment merits *human review*, never deployment or promotion.
"""
import math

from .metrics import paired_uncertainty


def assess_candidate(evaluation, attachment, baseline_scores, candidate_scores,
                     *, min_delta=0.08, resamples=10000, seed=20261024):
    """Fail closed unless runner, lineage and independently scored evidence agree."""
    if not isinstance(evaluation, dict) or not isinstance(attachment, dict):
        raise ValueError("Evaluation and attachment required")
    if evaluation.get("status") != "ELIGIBLE_FOR_HUMAN_REVIEW" or evaluation.get("error"):
        raise ValueError("Candidate not eligible for human review")
    if attachment.get("local_lineage_verified") is not True:
        raise ValueError("Verified local lineage required")
    if attachment.get("runner_status") != evaluation["status"]:
        raise ValueError("Runner status mismatch")
    for key in ("candidate_id", "base_revision", "lineage_hash"):
        value = evaluation.get(key)
        if not isinstance(value, str) or not value or attachment.get(key) != value:
            raise ValueError("Missing or mismatched experiment identity")
    if attachment.get("promotion") != "FORBIDDEN" or attachment.get("improvement_proven") is not False:
        raise ValueError("Attachment must not claim promotion or proof")
    if not isinstance(attachment.get("grader"), str) or not attachment["grader"].strip():
        raise ValueError("Independent grader identifier required")
    if attachment["grader"].strip().lower() in ("candidate", "self"):
        raise ValueError("Candidate cannot self-grade")
    if type(min_delta) not in (int, float) or not math.isfinite(min_delta) or not 0 < min_delta <= 1:
        raise ValueError("Invalid improvement threshold")
    metrics = paired_uncertainty(baseline_scores, candidate_scores,
                                 resamples=resamples, seed=seed)
    attached = attachment.get("metrics")
    if not isinstance(attached, dict) or attached.get("task_deltas") != metrics["task_deltas"]:
        raise ValueError("Attached scores do not match supplied paired evidence")
    if any(attached.get(k) != metrics[k] for k in
           ("task_count", "baseline_mean", "candidate_mean", "mean_delta")):
        raise ValueError("Attached metric summary mismatch")
    lower, upper = metrics["bootstrap_95_percentile_interval"]
    positive = metrics["mean_delta"] >= min_delta and lower > 0
    return {
        "candidate_id": evaluation["candidate_id"],
        "review_recommended": positive,
        "mean_delta": metrics["mean_delta"],
        "bootstrap_95_percentile_interval": [lower, upper],
        "threshold": min_delta,
        "promotion": "FORBIDDEN",
        "improvement_proven": False,
        "recursive_improvement_proven": False,
        "limitations": ("Task-bootstrap only. No grader authentication, task independence, "
                        "holdout custody, repeated-cycle transfer, or causal RSI validation."),
    }
