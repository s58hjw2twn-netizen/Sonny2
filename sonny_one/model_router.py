"""Provider-neutral, deterministic model selection; no network calls or billing.

Only models explicitly registered by the application can be selected. Provider
names and prices are caller-supplied metadata, never assumed live availability.
"""
from dataclasses import dataclass
from typing import Protocol

class TextModel(Protocol):
    def generate(self, *, system: str, user: str) -> str: ...

@dataclass(frozen=True)
class ModelOption:
    name: str
    model: TextModel
    tasks: frozenset[str]
    estimated_cost_units: int = 0
    enabled: bool = True

class ModelRouter:
    def __init__(self, options: list[ModelOption], *, max_cost_units: int = 0):
        if max_cost_units < 0:
            raise ValueError("max_cost_units must be nonnegative")
        if len({x.name for x in options}) != len(options):
            raise ValueError("duplicate model names")
        if any(x.estimated_cost_units < 0 for x in options):
            raise ValueError("negative model cost")
        self.options = tuple(options)
        self.max_cost_units = max_cost_units

    def select(self, task: str, *, preferred: str | None = None) -> ModelOption:
        if not task.strip():
            raise ValueError("task required")
        eligible = [x for x in self.options if x.enabled
                    and task in x.tasks
                    and x.estimated_cost_units <= self.max_cost_units]
        if preferred is not None:
            eligible = [x for x in eligible if x.name == preferred]
        if not eligible:
            raise LookupError("no authorized eligible model for task and budget")
        return min(eligible, key=lambda x: (x.estimated_cost_units, x.name))

    def generate(self, task: str, *, system: str, user: str,
                 preferred: str | None = None) -> tuple[str, str]:
        option = self.select(task, preferred=preferred)
        result = option.model.generate(system=system, user=user)
        if not isinstance(result, str):
            raise TypeError("model response must be text")
        return result, option.name
