"""Sonny ONE offline reference: not a production AI or deployed service."""
from dataclasses import dataclass, field
from typing import Protocol

class Model(Protocol):
    def generate(self, prompt: str) -> str: ...

class DemoModel:
    def generate(self, prompt: str) -> str:
        return f"Demo response: I received your request ({len(prompt)} characters). No external AI model is connected."

@dataclass
class SelfModel:
    identity: str = "Sonny ONE"
    model_type: str = "offline deterministic demo"
    limitations: tuple[str, ...] = ("No real-time knowledge", "No autonomous actions", "No consciousness claim")
    predictions: list[dict] = field(default_factory=list)

    def record_prediction(self, task: str, confidence: float) -> None:
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        self.predictions.append({"task": task, "confidence": confidence, "verified": False})

@dataclass
class ConsentMemory:
    enabled: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def remember(self, key: str, value: str) -> None:
        if not self.enabled:
            raise PermissionError("Memory requires explicit consent")
        if not isinstance(key, str) or not isinstance(value, str) or not key or len(key) > 128 or len(value) > 2000:
            raise ValueError("Invalid memory entry")
        self.facts[key] = value

    def forget(self, key: str) -> None:
        self.facts.pop(key, None)

@dataclass
class Sonny:
    model: Model = field(default_factory=DemoModel)
    self_model: SelfModel = field(default_factory=SelfModel)
    memory: ConsentMemory = field(default_factory=ConsentMemory)

    def respond(self, user_input: str) -> str:
        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("Input cannot be empty")
        if len(user_input) > 8000:
            raise ValueError("Input too long")
        # Memory deliberately not interpolated: retrieval requires user isolation and policy.
        return self.model.generate(user_input)
