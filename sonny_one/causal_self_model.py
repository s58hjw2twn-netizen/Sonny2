"""Sonny ONE causal self-model research prototype.

Tracks declared capabilities, task predictions and observed outcomes. A prediction
is not evidence of success. No model calls, external actions or self-modification.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class Prediction:
    task_id: str
    capability: str
    probability: float
    rationale: str


@dataclass(frozen=True)
class Observation:
    task_id: str
    succeeded: bool
    evidence_id: str


class CausalSelfModel:
    def __init__(self, capabilities: Mapping[str, bool]):
        if not capabilities or any(not isinstance(k, str) or not k or type(v) is not bool
                                   for k, v in capabilities.items()):
            raise ValueError("capabilities must be nonempty boolean declarations")
        self._capabilities = dict(capabilities)
        self._predictions: dict[str, Prediction] = {}
        self._observations: dict[str, Observation] = {}

    def predict(self, task_id: str, capability: str, probability: float,
                rationale: str) -> Prediction:
        if not task_id or not rationale or capability not in self._capabilities:
            raise ValueError("task, rationale and known capability required")
        if task_id in self._predictions:
            raise ValueError("duplicate task")
        if not isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("probability must be finite and between zero and one")
        if not self._capabilities[capability]:
            raise PermissionError("capability is not enabled")
        prediction = Prediction(task_id, capability, probability, rationale)
        self._predictions[task_id] = prediction
        return prediction

    def observe(self, task_id: str, succeeded: bool, evidence_id: str) -> Observation:
        if task_id not in self._predictions or task_id in self._observations:
            raise ValueError("unknown or already observed task")
        if type(succeeded) is not bool or not evidence_id:
            raise ValueError("verified boolean outcome and evidence reference required")
        observation = Observation(task_id, succeeded, evidence_id)
        self._observations[task_id] = observation
        return observation

    def report(self) -> dict:
        paired = [(self._predictions[k], v) for k, v in self._observations.items()]
        n = len(paired)
        return {
            "capabilities": dict(self._capabilities),
            "predictions": len(self._predictions),
            "observed": n,
            "unobserved": len(self._predictions) - n,
            "brier_score": (sum((p.probability - int(o.succeeded)) ** 2
                                for p, o in paired) / n if n else None),
            "outcomes": [
                {"prediction": asdict(p), "observation": asdict(o)}
                for p, o in paired
            ],
            "self_awareness_verified": False,
            "evidence_authentication": "external_review_required",
        }
