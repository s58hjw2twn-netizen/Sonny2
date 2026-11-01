"""Evidence-oriented functional self-model experiments.

A model can report beliefs and predictions about itself, but those reports
are hypotheses, not evidence of subjective consciousness.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SelfPrediction:
    experiment_id: str
    predicted_success_probability: float
    observed_success: bool
    source_digest: str


def calibration_metrics(predictions: list[SelfPrediction]) -> dict:
    if not predictions:
        return {"status": "INSUFFICIENT_DATA", "sample_size": 0}
    ids = set()
    errors = []
    for item in predictions:
        if not isinstance(item, SelfPrediction):
            raise TypeError("SelfPrediction required")
        if not item.experiment_id or item.experiment_id in ids or not item.source_digest:
            raise ValueError("missing or duplicate evidence")
        ids.add(item.experiment_id)
        p = item.predicted_success_probability
        if isinstance(p, bool) or not isinstance(p, (float, int)) or not 0 <= p <= 1:
            raise ValueError("invalid probability")
        if type(item.observed_success) is not bool:
            raise ValueError("observed outcome must be boolean")
        errors.append((p - int(item.observed_success)) ** 2)
    return {"status": "MEASURED_FUNCTIONAL_CALIBRATION",
            "sample_size": len(errors),
            "brier_score": sum(errors) / len(errors),
            "subjective_consciousness_established": False}
