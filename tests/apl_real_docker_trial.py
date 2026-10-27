"""GitHub-hosted, non-production APL trial. Two separate CI jobs execute this script.
No generated patch is committed, merged, or deployed.
"""
import hashlib
import json
import os
import subprocess
import sys
import statistics
import time
from pathlib import Path

from sonny_one.apl.provenance import verify_report_lineage
from sonny_one.apl.policy import append_lineage
from sonny_one.apl.runner import evaluate

root = Path.cwd()
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
source = root
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
target = root / "sonny_one/apl_targets/offline_strategy.py"
original = target.read_text()
# Candidate replaces a full sort with a minimum scan in an experimental-only function.
# Correctness tests alone do not establish a measured performance improvement.
try:
    before = "    return sorted(values)[0]"
    after = "    return min(values)"
    if original.count(before) != 1:
        raise RuntimeError("Expected baseline function not found")
    target.write_text(original.replace(before, after))
    diff = subprocess.check_output(["git", "diff", "--", str(target.relative_to(root))], text=True)
finally:
    target.write_text(original)
if not diff.startswith("diff --git "):
    raise RuntimeError("Candidate patch not generated")
patch = out / "candidate.diff"
patch.write_text(diff)
trusted = out / "trusted"
heldout = out / "heldout"
trusted.mkdir()
heldout.mkdir()
(trusted / "test_mean.py").write_text("""import unittest
from sonny_one.apl_targets.offline_strategy import mean
class TestMean(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(mean([1, 2, 3]), 2)
""")
(heldout / "test_extremes.py").write_text("""import unittest
from sonny_one.apl_targets.offline_strategy import smallest, largest
class TestExtremes(unittest.TestCase):
    def test_extremes(self):
        self.assertEqual(smallest([4, 1, 3]), 1)
        self.assertEqual(largest([4, 1, 3]), 4)
    def test_minimum_duplicate_and_negative(self):
        self.assertEqual(smallest([3, -2, -2, 5]), -2)
    def test_minimum_singleton(self):
        self.assertEqual(smallest([42]), 42)
    def test_minimum_large_reversed(self):
        self.assertEqual(smallest(list(range(10000, -1, -1))), 0)
""")
image = subprocess.check_output(
    ["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}",
     "python:3.11-slim"], text=True).strip()
ledger = out / "ledger.jsonl"
append_lineage(ledger, {"replica_id": os.environ["APL_REPLICA_ID"],
                        "github_run_id": os.environ["GITHUB_RUN_ID"],
                        "github_job": os.environ["GITHUB_JOB"],
                        "github_sha": os.environ["GITHUB_SHA"],
                        "github_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"]})
report = evaluate(source, revision, patch, trusted, heldout, image, ledger,
                  timeout=75, framework="unittest")
(out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
if not verify_report_lineage(report, ledger):
    raise RuntimeError("Local lineage verification failed")
if report["status"] != "ELIGIBLE_FOR_HUMAN_REVIEW" or report["promotion"] != "FORBIDDEN":
    raise RuntimeError("Real Docker trial failed: " + str(report.get("error", report)))
for name in ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout"):
    if report[name]["exit_code"] != 0:
        raise RuntimeError("Docker test failure: " + name)
# Controlled local benchmark, run only after both correctness suites succeed.
# Alternating order reduces systematic first-run advantage; results are
# descriptive only because shared CI hosts have uncontrolled noise.
import importlib.util
import tempfile
with tempfile.TemporaryDirectory(prefix="apl-perf-") as scratch:
    baseline_file = Path(scratch) / "baseline.py"
    candidate_file = Path(scratch) / "candidate.py"
    baseline_file.write_text(original)
    candidate_file.write_text(original.replace("    return sorted(values)[0]", "    return min(values)"))
    def load_function(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.smallest
    funcs = {"baseline": load_function(baseline_file, "apl_base"),
             "candidate": load_function(candidate_file, "apl_candidate")}
    inputs = [list(range(12000, 0, -1)),
              list(range(-6000, 6000))]
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
            if results != [expected[0]] * 20 + [expected[1]] * 20:
                raise RuntimeError("Benchmark postcheck failed")
            timings[label].append(elapsed)
    medians = {label: statistics.median(values) for label, values in timings.items()}
    benchmark = {"method": "alternating_wall_clock_ns_prepostcheck",
                 "rounds": 12, "calls_per_round": len(inputs) * 20,
                 "baseline_median_ns": medians["baseline"],
                 "candidate_median_ns": medians["candidate"],
                 "candidate_over_baseline_ratio": medians["candidate"] / medians["baseline"],
                 "shared_runner_noise_uncontrolled": True,
                 "independent_external_benchmark_verified": False,
                 "promotion_allowed": False}
    (out / "benchmark.json").write_text(json.dumps(benchmark, sort_keys=True, indent=2))
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (out / "report.json", ledger, patch, out / "benchmark.json")}
(out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2))
print("Real algorithm-change candidate passed four Docker suite executions; performance improvement not proven")
