"""Trusted, deterministic-shape microbenchmark run INSIDE restricted Docker.

Input source modules are experimental; never import them on the CI host.
Wall-clock timings on shared runners are descriptive, not causal RSI evidence.
"""
import importlib.util
import json
import random
import statistics
import time
from pathlib import Path

root = Path("/bench")


def load_function(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.smallest


funcs = {
    "baseline": load_function(root / "baseline.py", "apl_base"),
    "candidate": load_function(root / "candidate.py", "apl_candidate"),
}
rng = random.Random(1729)
shuffled = list(range(12000))
rng.shuffle(shuffled)
inputs = [list(range(12000, 0, -1)),
          list(range(-6000, 6000)), shuffled]
expected = [min(values) for values in inputs]
for fn in funcs.values():
    for values, answer in zip(inputs, expected):
        if fn(values) != answer:
            raise RuntimeError("Benchmark precheck failed")

timings = {"baseline": [], "candidate": []}
for round_no in range(12):
    for label in (("baseline", "candidate") if round_no % 2 == 0
                  else ("candidate", "baseline")):
        fn = funcs[label]
        start = time.perf_counter_ns()
        results = []
        for values in inputs:
            for _ in range(20):
                results.append(fn(values))
        elapsed = time.perf_counter_ns() - start
        if results != [answer for answer in expected for _ in range(20)]:
            raise RuntimeError("Benchmark postcheck failed")
        timings[label].append(elapsed)

shape_timings = {}
for shape, values, answer in zip(("descending", "ascending", "seeded_shuffled"),
                                 inputs, expected):
    per_shape = {"baseline": [], "candidate": []}
    for round_no in range(12):
        for label in (("baseline", "candidate") if round_no % 2 == 0
                      else ("candidate", "baseline")):
            fn = funcs[label]
            start = time.perf_counter_ns()
            results = [fn(values) for _ in range(20)]
            elapsed = time.perf_counter_ns() - start
            if results != [answer] * 20:
                raise RuntimeError("Shape benchmark correctness mismatch")
            per_shape[label].append(elapsed)
    base = statistics.median(per_shape["baseline"])
    candidate = statistics.median(per_shape["candidate"])
    shape_timings[shape] = {
        "baseline_median_ns": base,
        "candidate_median_ns": candidate,
        "candidate_over_baseline_ratio": candidate / base,
    }

medians = {label: statistics.median(values) for label, values in timings.items()}
report = {
    "method": "alternating_wall_clock_ns_prepostcheck",
    "rounds": 12,
    "calls_per_round": len(inputs) * 20,
    "input_shapes": ["descending", "ascending", "seeded_shuffled"],
    "shape_timings": shape_timings,
    "seed": 1729,
    "baseline_median_ns": medians["baseline"],
    "candidate_median_ns": medians["candidate"],
    "candidate_over_baseline_ratio": medians["candidate"] / medians["baseline"],
    "shared_runner_noise_uncontrolled": True,
    "independent_external_benchmark_verified": False,
    "promotion_allowed": False,
}
print(json.dumps(report, sort_keys=True))
