"""Leakage-resistant, read-only comparison of preregistered predictions.

No model updates; outcomes must be independently verified before use.
"""
from __future__ import annotations
from math import isfinite


def compare_holdout(baseline: list[float], candidate: list[float], outcomes: list[bool], *, minimum: int = 20) -> dict:
    if type(minimum) is not int or minimum < 2:
        raise ValueError('invalid minimum')
    if not isinstance(baseline, list) or not isinstance(candidate, list) or not isinstance(outcomes, list):
        raise ValueError('lists required')
    if not (len(baseline) == len(candidate) == len(outcomes)) or not baseline:
        raise ValueError('paired nonempty records required')
    if any(type(y) is not bool for y in outcomes):
        raise ValueError('binary verified outcomes required')
    if any(type(p) not in (int, float) or not isfinite(p) or not 0 <= p <= 1 for p in baseline + candidate):
        raise ValueError('invalid probability')
    n = len(outcomes)
    base = sum((p - int(y))**2 for p, y in zip(baseline, outcomes)) / n
    cand = sum((p - int(y))**2 for p, y in zip(candidate, outcomes)) / n
    return {'samples': n, 'baseline_brier': base, 'candidate_brier': cand,
            'delta_brier': cand-base, 'direction': 'insufficient_evidence' if n < minimum else
            'candidate_better_descriptively' if cand < base else
            'candidate_worse_descriptively' if cand > base else 'tied',
            'statistical_significance_established': False,
            'outcomes_independently_authenticated': False,
            'changes_applied': False}
