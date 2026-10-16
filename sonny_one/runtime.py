"""Minimal isolated Sonny ONE research runtime.

No network access, autonomous model calls, or production authentication.
"""
from dataclasses import dataclass
from sonny_one.core import Identity, EmotionalSimulation
from sonny_one.life_memory import LifeMemory
from sonny_one.memory_policy import MemoryCandidate, MemoryStatus
from sonny_one.learning import Experience, propose_strategies

@dataclass(frozen=True)
class SessionResult:
    identity: str
    recalled: tuple[str, ...]
    proposed_strategies: tuple[str, ...]
    emotional_simulation: dict[str, float]

class SonnyOneRuntime:
    def __init__(self, memory_path: str):
        self.identity = Identity()
        self.memory = LifeMemory(memory_path)
        self.emotions = EmotionalSimulation()
        self.experiences: list[Experience] = []

    def remember_confirmed(self, user_id: str, statement: str, source: str, *, consent: bool) -> int:
        return self.memory.add(MemoryCandidate(
            user_id, source, statement, MemoryStatus.VALIDATED, 1.0, consent))

    def record_outcome(self, experience: Experience) -> None:
        self.experiences.append(experience)

    def inspect(self, user_id: str, *, uncertainty: float = 0.5, novelty: float = 0.5) -> SessionResult:
        self.emotions.update(uncertainty=uncertainty, novelty=novelty)
        proposals = propose_strategies(self.experiences)
        return SessionResult(
            self.identity.agent_id,
            tuple(record.statement for record in self.memory.recall(user_id)),
            tuple(p.strategy for p in proposals),
            {"curiosity": self.emotions.curiosity,
             "caution": self.emotions.caution,
             "engagement": self.emotions.engagement},
        )
