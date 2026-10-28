"""Read-only empirical calibration of a Sonny ONE causal self-model.

Only observed outcomes are scored. Recommendations do not change model weights,
permissions, stored predictions, or authorize actions. Requires external evidence
review before treating results as trustworthy.
"""
from __future__ import annotations


def calibration_report(model, *, min_samples: int = 5) -> dict:
    if type(min_samples) is not int or min_samples < 2:
        raise ValueError('min_samples must be an integer >= 2')
    report = model.report()
    groups: dict[str, list[tuple[float, int]]] = {}
    for item in report['outcomes']:
        p, o = item['prediction'], item['observation']
        groups.setdefault(p['capability'], []).append((p['probability'], int(o['succeeded'])))
    results = {}
    for capability, pairs in sorted(groups.items()):
        n = len(pairs)
        predicted = sum(p for p, _ in pairs) / n
        observed = sum(y for _, y in pairs) / n
        brier = sum((p-y)**2 for p, y in pairs) / n
        results[capability] = {
            'samples': n, 'mean_predicted_success': predicted,
            'observed_success': observed, 'brier_score': brier,
            'calibration_gap': predicted - observed,
            'recommendation': ('insufficient_evidence' if n < min_samples else
                               'review_overconfidence' if predicted-observed > 0.15 else
                               'review_underconfidence' if observed-predicted > 0.15 else
                               'monitor'),
        }
    return {'capabilities': results, 'unobserved': report['unobserved'],
            'minimum_samples': min_samples, 'changes_applied': False,
            'outcomes_independently_authenticated': False}
