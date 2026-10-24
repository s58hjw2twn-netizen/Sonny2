"""Conservative metric evidence for paired APL experiments.

This module never changes code, promotes a candidate, or interprets missing
measurements as success. Measurements must come from an independent grader.
"""
import math


def compare_metrics(baseline: dict, candidate: dict) -> dict:
    """Compare aligned per-task 0..1 scores; no statistical significance claim."""
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        raise ValueError("Both metric reports must be objects")
    if not baseline or baseline.keys() != candidate.keys():
        raise ValueError("Reports require identical, nonempty task identifiers")
    deltas = {}
    for task in sorted(baseline):
        b, c = baseline[task], candidate[task]
        for value in (b, c):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Scores must be finite numbers in [0, 1]")
        deltas[task] = c - b
    mean_delta = sum(deltas.values()) / len(deltas)
    return {
        "task_count": len(deltas),
        "baseline_mean": sum(baseline.values()) / len(deltas),
        "candidate_mean": sum(candidate.values()) / len(deltas),
        "mean_delta": mean_delta,
        "improved_tasks": sum(v > 0 for v in deltas.values()),
        "regressed_tasks": sum(v < 0 for v in deltas.values()),
        "unchanged_tasks": sum(v == 0 for v in deltas.values()),
        "task_deltas": deltas,
        "statistically_significant": None,
        "improvement_proven": False,
        "promotion": "FORBIDDEN",
        "note": "Descriptive paired scores only; independent grading, holdout integrity and uncertainty analysis required."
    }
