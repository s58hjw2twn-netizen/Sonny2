"""Explicit local-only benchmark runner; never downloads or activates a model.

A caller supplies a provider and fixed benchmark cases. The runner does not
persist prompts, change model routing, or touch frozen research fixtures.
"""
from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from sonny_one.inference import Request, generate
from sonny_one.local_model_benchmark import Trial, summarize


@dataclass(frozen=True)
class BenchmarkCase:
    task_id: str
    prompt: str
    expected: str

    def __post_init__(self):
        if not isinstance(self.task_id, str) or not self.task_id.strip() or len(self.task_id) > 128:
            raise ValueError("Invalid task identifier")
        Request(self.prompt)
        if not isinstance(self.expected, str) or not self.expected.strip() or len(self.expected) > 4000:
            raise ValueError("Invalid expected answer")


def run_local_benchmark(
    provider,
    model_id: str,
    cases: list[BenchmarkCase],
    *,
    repetitions: int = 1,
    timeout_seconds: float = 20.0,
    clock: Callable[[], float] = perf_counter,
) -> tuple[list[Trial], dict]:
    """Run bounded sequential trials; caller must approve and start execution.

    Failures abort the run rather than being silently counted as incorrect.
    Returned trials contain responses; handle them as potentially sensitive.
    """
    if not isinstance(model_id, str) or not model_id.strip() or len(model_id) > 128:
        raise ValueError("Invalid model identifier")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or not 1 <= repetitions <= 5:
        raise ValueError("Repetitions must be between 1 and 5")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 100:
        raise ValueError("Provide 1 to 100 benchmark cases")
    if any(not isinstance(case, BenchmarkCase) for case in cases):
        raise TypeError("Invalid benchmark case")
    if len({case.task_id for case in cases}) != len(cases):
        raise ValueError("Duplicate task identifiers")
    Request("validation", timeout_seconds=timeout_seconds)
    trials = []
    for _ in range(repetitions):
        for case in cases:
            start = clock()
            response = generate(provider, case.prompt, timeout_seconds=timeout_seconds)
            elapsed = (clock() - start) * 1000
            if response.model_id != model_id:
                raise ValueError("Unexpected model identifier")
            if response.demo:
                raise ValueError("Demo responses cannot be benchmarked as real AI")
            trials.append(Trial(case.task_id, model_id, case.expected, response.text, elapsed))
    return trials, summarize(trials)[model_id]
