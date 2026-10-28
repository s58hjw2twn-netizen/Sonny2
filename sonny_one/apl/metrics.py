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
    if any(not isinstance(task, str) or not task.strip() for task in baseline):
        raise ValueError("Task identifiers must be nonempty strings")
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


def paired_uncertainty(baseline: dict, candidate: dict, *, resamples=10000, seed=20261024) -> dict:
    """Seeded task-paired percentile bootstrap, conditional on supplied scores.

Assumes independent, representative tasks. Correlated tasks/reused holdouts
invalidate that interpretation; this does not measure repeat-run variability.
"""
    import random
    summary = compare_metrics(baseline, candidate)
    if type(resamples) is not int or not 100 <= resamples <= 100000:
        raise ValueError("Resamples must be an integer in [100, 100000]")
    if type(seed) is not int:
        raise ValueError("Seed must be an integer")
    values = list(summary['task_deltas'].values())
    if len(values) < 2:
        raise ValueError("At least two paired tasks are required")
    if resamples * len(values) > 10_000_000:
        raise ValueError("Bootstrap computation budget exceeded")
    rng = random.Random(seed)
    samples = sorted(sum(rng.choice(values) for _ in values) / len(values)
                     for _ in range(resamples))
    return {**summary, 'bootstrap_95_percentile_interval':
            [samples[int(.025 * (resamples - 1))], samples[int(.975 * (resamples - 1))]],
            'resamples': resamples, 'seed': seed,
            'uncertainty_scope': 'Task sampling only, conditional on supplied scores; no independence or repeat-run validation.'}
