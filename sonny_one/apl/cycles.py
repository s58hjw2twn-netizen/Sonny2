"""Read-only repeated-cycle champion/challenger evidence assessment.

All cycles must use separately identified evaluation material. No model is
trained, no patches are applied, and no candidate is automatically promoted.
"""
from .review_gate import assess_candidate


def assess_cycles(cycles, *, min_cycles=3, min_delta=0.08, resamples=1000, seed=20261024):
    if type(min_cycles) is not int or not 2 <= min_cycles <= 20:
        raise ValueError("Cycle minimum must be an integer in [2, 20]")
    if not isinstance(cycles, list) or not min_cycles <= len(cycles) <= 20:
        raise ValueError("Insufficient or excessive evaluation cycles")
    seen_cycles, seen_suites, seen_candidates = set(), set(), set()
    reports = []
    for index, cycle in enumerate(cycles):
        if not isinstance(cycle, dict) or set(cycle) != {
            "cycle_id", "suite_fingerprint", "evaluation", "attachment",
            "baseline_scores", "candidate_scores"
        }:
            raise ValueError("Cycle has missing or unexpected fields")
        cycle_id, suite = cycle["cycle_id"], cycle["suite_fingerprint"]
        if not isinstance(cycle_id, str) or not cycle_id.strip() or cycle_id in seen_cycles:
            raise ValueError("Cycle IDs must be unique and nonempty")
        if not isinstance(suite, str) or len(suite) != 64 or any(
            ch not in "0123456789abcdef" for ch in suite
        ) or suite in seen_suites:
            raise ValueError("Unique SHA-256 suite fingerprints required")
        seen_cycles.add(cycle_id)
        seen_suites.add(suite)
        evaluation = cycle["evaluation"]
        if not isinstance(evaluation, dict):
            raise ValueError("Invalid evaluation")
        candidate_id = evaluation.get("candidate_id")
        if candidate_id in seen_candidates:
            raise ValueError("Repeated candidate identity")
        seen_candidates.add(candidate_id)
        result = assess_candidate(
            evaluation, cycle["attachment"], cycle["baseline_scores"],
            cycle["candidate_scores"], min_delta=min_delta,
            resamples=resamples, seed=seed + index
        )
        reports.append({"cycle_id": cycle_id, "suite_fingerprint": suite, **result})
    all_positive = all(item["review_recommended"] for item in reports)
    return {
        "cycle_count": len(reports),
        "all_cycles_positive": all_positive,
        "human_review_recommended": all_positive,
        "cycles": reports,
        "promotion": "FORBIDDEN",
        "improvement_proven": False,
        "recursive_improvement_proven": False,
        "limitations": (
            "Distinct suite fingerprints do not prove independent tasks, custody, "
            "causal self-improvement, or cross-cycle model evolution. "
            "External independent replication remains necessary."
        ),
    }
