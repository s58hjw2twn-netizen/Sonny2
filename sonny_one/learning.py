"""Outcome-based strategy proposals; never self-executes or self-promotes."""
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Experience:
    task_family: str
    strategy: str
    succeeded: bool
    verified: bool
    source: str

@dataclass(frozen=True)
class StrategyProposal:
    task_family: str
    strategy: str
    verified_trials: int
    observed_success_rate: float
    status: str = "candidate-only"

def propose_strategies(experiences: Iterable[Experience], *, min_trials: int = 5) -> list[StrategyProposal]:
    if min_trials < 2:
        raise ValueError("min_trials must be at least 2")
    grouped: dict[tuple[str,str],list[bool]] = {}
    for item in experiences:
        if not item.verified or not item.source or not item.task_family or not item.strategy:
            continue
        grouped.setdefault((item.task_family,item.strategy),[]).append(item.succeeded)
    return [StrategyProposal(family,strategy,len(results),sum(results)/len(results))
            for (family,strategy),results in sorted(grouped.items())
            if len(results)>=min_trials]
