"""Descriptive failure-target repair diagnostic for bounded APL experiments.

This does not establish causal directedness or generalization. Task outcomes
must be supplied by a trusted evaluator, not by candidate-generated reports.
"""


def _outcomes(parent, candidate, *, name):
    if (not isinstance(parent, dict) or not parent or
            not isinstance(candidate, dict) or parent.keys() != candidate.keys()):
        raise ValueError(f"{name} requires matching nonempty task sets")
    if any(not isinstance(task, str) or not task.strip() for task in parent):
        raise ValueError(f"{name} task identifiers must be nonempty strings")
    if any(type(value) is not bool for outcomes in (parent, candidate)
           for value in outcomes.values()):
        raise ValueError(f"{name} outcomes must be booleans")


def assess_target_repair(parent, candidate, *, target_task,
                         heldout_parent=None, heldout_candidate=None):
    """Compare target repair with repair of other parent failures.

    Returns descriptive fractions, not a statistical test. Held-out tasks must
    be disjoint and are not used to select candidates. Caller is responsible
    for trusted evaluation, preregistration and task independence.
    """
    _outcomes(parent, candidate, name="Development")
    if not isinstance(target_task, str) or target_task not in parent:
        raise ValueError("Target task is not in the development task set")
    if parent[target_task] is not False:
        raise ValueError("Target must be a preregistered parent failure")
    other_failures = [t for t in parent if t != target_task and parent[t] is False]
    if not other_failures:
        raise ValueError("At least one other parent failure is required")
    other_repairs = sum(candidate[t] is True for t in other_failures)
    target_repaired = candidate[target_task] is True
    regression_count = sum(parent[t] is True and candidate[t] is False for t in parent)
    heldout = None
    if heldout_parent is not None or heldout_candidate is not None:
        _outcomes(heldout_parent, heldout_candidate, name="Held-out")
        if not parent.keys().isdisjoint(heldout_parent.keys()):
            raise ValueError("Held-out tasks must not overlap development tasks")
        gained = sum(not heldout_parent[t] and heldout_candidate[t] for t in heldout_parent)
        lost = sum(heldout_parent[t] and not heldout_candidate[t] for t in heldout_parent)
        heldout = {"task_count": len(heldout_parent), "gained_passes": gained,
                   "lost_passes": lost, "net_pass_delta": gained - lost,
                   "net_pass_rate_delta": (gained - lost) / len(heldout_parent)}
    other_rate = other_repairs / len(other_failures)
    return {
        "target_task": target_task,
        "target_repaired": target_repaired,
        "other_parent_failure_count": len(other_failures),
        "other_parent_failures_repaired": other_repairs,
        "other_failure_repair_rate": other_rate,
        "target_minus_other_repair_rate": int(target_repaired) - other_rate,
        "development_regressions": regression_count,
        "heldout": heldout,
        "causal_directedness_proven": False,
        "generalization_proven": False,
        "improvement_proven": False,
        "promotion": "FORBIDDEN",
        "limitations": "Single-target descriptive contrast; not a randomized or independent evaluation. "
                       "Holdout results are descriptive and must not be fed into candidate generation."
    }
