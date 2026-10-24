"""Offline, deterministic evaluation of candidate text-model outputs.

This module performs no network calls, model downloads, or automatic
promotion. Input is a JSON-compatible list of benchmark items with an
explicit expected answer and one or more candidate model answers.
"""
from dataclasses import dataclass
import math
import statistics


@dataclass(frozen=True)
class Trial:
    task_id: str
    model_id: str
    expected: str
    actual: str
    latency_ms: float

    def __post_init__(self):
        if any(not isinstance(x, str) or not x.strip() or len(x) > 4000
               for x in (self.task_id, self.model_id, self.expected, self.actual)):
            raise ValueError("Invalid benchmark trial text")
        if not isinstance(self.latency_ms, (int, float)) or isinstance(self.latency_ms, bool) or not math.isfinite(self.latency_ms) or self.latency_ms < 0:
            raise ValueError("Invalid latency")


def normalize(text: str) -> str:
    """Conservative normalization; not semantic or judge-model grading."""
    return " ".join(text.casefold().split())


def summarize(trials: list[Trial]) -> dict:
    if not trials:
        raise ValueError("At least one trial required")
    if len(trials) > 10000:
        raise ValueError("Too many trials")
    models = {}
    for trial in trials:
        models.setdefault(trial.model_id, []).append(trial)
    report = {}
    for model, items in sorted(models.items()):
        hits = sum(normalize(x.expected) == normalize(x.actual) for x in items)
        latencies = [float(x.latency_ms) for x in items]
        report[model] = {
            "trials": len(items),
            "exact_match_count": hits,
            "exact_match_rate": round(hits / len(items), 6),
            "median_latency_ms": round(statistics.median(latencies), 3),
            "max_latency_ms": round(max(latencies), 3),
            "task_ids": sorted({x.task_id for x in items}),
        }
    return report


def comparable_models(trials: list[Trial]) -> bool:
    """True only if models cover identical task IDs and repetitions."""
    from collections import Counter
    groups = {}
    for item in trials:
        groups.setdefault(item.model_id, Counter())[item.task_id] += 1
    return len(groups) >= 2 and len({tuple(sorted(c.items())) for c in groups.values()}) == 1
