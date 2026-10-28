"""Experimental champion/challenger evaluation; no automatic deployment."""
from dataclasses import dataclass
from typing import Mapping

FROZEN_REFERENCES = ("SEB-1.0", "CSAT-1.3", "Sonny-RSI-v1.3")

@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    benchmark_id: str
    scores: Mapping[str, float]
    independent: bool
    sealed_holdout: bool
    regressions: int

    def validate(self) -> None:
        if not self.candidate_id or not self.benchmark_id:
            raise ValueError("Candidate and benchmark IDs required")
        if not self.scores or any(not 0 <= v <= 1 for v in self.scores.values()):
            raise ValueError("All scores must be in [0,1]")
        if self.regressions < 0:
            raise ValueError("Regressions cannot be negative")

@dataclass(frozen=True)
class PromotionDecision:
    status: str
    reason: str

def evaluate_challenger(champion: Evaluation, challenger: Evaluation, *, owner_approved: bool = False) -> PromotionDecision:
    champion.validate()
    challenger.validate()
    if champion.candidate_id == challenger.candidate_id:
        return PromotionDecision("reject", "Same candidate in both arms")
    if champion.benchmark_id != challenger.benchmark_id or set(champion.scores) != set(challenger.scores):
        return PromotionDecision("reject", "Unmatched evaluation design")
    if not challenger.independent or not challenger.sealed_holdout:
        return PromotionDecision("hold", "Independent sealed evaluation required")
    if challenger.regressions > champion.regressions:
        return PromotionDecision("reject", "Regression count increased")
    if any(challenger.scores[k] < champion.scores[k] for k in champion.scores):
        return PromotionDecision("reject", "Metric regression")
    if not any(challenger.scores[k] > champion.scores[k] for k in champion.scores):
        return PromotionDecision("reject", "No measured improvement")
    if not owner_approved:
        return PromotionDecision("hold", "Owner approval required")
    return PromotionDecision("eligible", "Eligible for separate manual integration review")
