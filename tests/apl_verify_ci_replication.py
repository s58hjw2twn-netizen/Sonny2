"""Read-only cross-job artifact verifier. No promotion, commit, merge or deployment."""
import hashlib
import json
import os
import sys
from pathlib import Path

from sonny_one.apl.provenance import verify_report_lineage

root = Path(sys.argv[1])
reports = []
job_records = []
benchmarks = []
for name in ("alpha", "beta"):
    directory = root / ("apl-real-" + name)
    manifest = json.loads((directory / "manifest.json").read_text())
    for filename in ("report.json", "ledger.jsonl", "candidate.diff", "benchmark.json"):
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != manifest[filename]:
            raise RuntimeError("Evidence manifest mismatch: " + name + "/" + filename)
    report = json.loads((directory / "report.json").read_text())
    if not verify_report_lineage(report, directory / "ledger.jsonl"):
        raise RuntimeError("Invalid lineage for " + name)
    ledger_lines = (directory / "ledger.jsonl").read_text().splitlines()
    first = json.loads(ledger_lines[0])
    if first.get("replica_id") != name:
        raise RuntimeError("Incorrect replica job label")
    for key, env in (("github_run_id", "GITHUB_RUN_ID"),
                     ("github_sha", "GITHUB_SHA"),
                     ("github_run_attempt", "GITHUB_RUN_ATTEMPT")):
        if str(first.get(key)) != os.environ[env]:
            raise RuntimeError("Evidence CI identity mismatch: " + name + "/" + key)
    if first.get("github_job") != "replica":
        raise RuntimeError("Evidence originated from unexpected CI job")
    if report["base_revision"] != os.environ["GITHUB_SHA"]:
        raise RuntimeError("Report base revision differs from CI checkout")
    if hashlib.sha256((directory / "candidate.diff").read_bytes()).hexdigest() != report["candidate_id"]:
        raise RuntimeError("Candidate patch digest mismatch")
    job_records.append(first)
    if report["status"] != "ELIGIBLE_FOR_HUMAN_REVIEW" or report["promotion"] != "FORBIDDEN":
        raise RuntimeError("Replica not eligible for human review: " + name)
    for suite in ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout"):
        if report[suite]["exit_code"] != 0:
            raise RuntimeError("Nonzero Docker test exit: " + name + "/" + suite)
    benchmark = json.loads((directory / "benchmark.json").read_text())
    if benchmark["rounds"] != 12 or benchmark["calls_per_round"] != 60:
        raise RuntimeError("Benchmark protocol mismatch")
    if not 0 < benchmark["candidate_over_baseline_ratio"] < 100:
        raise RuntimeError("Invalid benchmark ratio")
    if benchmark.get("input_shapes") != ["descending", "ascending", "seeded_shuffled"] or benchmark.get("seed") != 1729:
        raise RuntimeError("Benchmark input protocol mismatch")
    for shape in benchmark["input_shapes"]:
        record = benchmark.get("shape_timings", {}).get(shape)
        if not isinstance(record, dict):
            raise RuntimeError("Missing shape-level timing: " + shape)
        base = record.get("baseline_median_ns")
        candidate = record.get("candidate_median_ns")
        if not all(isinstance(x, (int, float)) and x > 0 for x in (base, candidate)):
            raise RuntimeError("Invalid shape-level timing: " + shape)
        if abs(candidate / base - record.get("candidate_over_baseline_ratio", -1)) > 1e-9:
            raise RuntimeError("Incorrect shape-level ratio: " + shape)
    for metric in ("baseline_median_ns", "candidate_median_ns"):
        if not isinstance(benchmark[metric], (int, float)) or benchmark[metric] <= 0:
            raise RuntimeError("Invalid timing measurement: " + metric)
    measured_ratio = benchmark["candidate_median_ns"] / benchmark["baseline_median_ns"]
    if abs(measured_ratio - benchmark["candidate_over_baseline_ratio"]) > 1e-9:
        raise RuntimeError("Reported timing ratio does not match measured medians")
    if benchmark.get("shared_runner_noise_uncontrolled") is not True:
        raise RuntimeError("Shared-runner uncertainty must remain explicit")
    if benchmark.get("independent_external_benchmark_verified") is not False:
        raise RuntimeError("External benchmark verification is not established")
    if benchmark["promotion_allowed"] is not False:
        raise RuntimeError("Benchmark must not permit promotion")
    benchmarks.append(benchmark)
    reports.append(report)
identity = ("candidate_id", "base_revision", "image",
            "trusted_suite_sha256", "heldout_suite_sha256", "test_framework")
if any(reports[0][key] != reports[1][key] for key in identity):
    raise RuntimeError("Replicas disagree on candidate, image, revision or frozen suites")
if job_records[0]["replica_id"] == job_records[1]["replica_id"]:
    raise RuntimeError("Replicas have identical job labels")
if reports[0]["lineage_hash"] == reports[1]["lineage_hash"]:
    raise RuntimeError("Replicas reused lineage")
print(json.dumps({"two_distinct_ci_jobs": True, "docker_suites_passed": True,
                  "candidate_over_baseline_ratios": [b["candidate_over_baseline_ratio"] for b in benchmarks],
                  "performance_result_descriptive_only": True,
                  "per_shape_ratios": [{shape: b["shape_timings"][shape]["candidate_over_baseline_ratio"] for shape in b["input_shapes"]} for b in benchmarks],
                  "github_artifact_manifest_verified": True,
                  "independent_external_custodian_verified": False,
                  "scientific_improvement_proven": False,
                  "unattended_commit_allowed": False,
                  "promotion_allowed": False}, indent=2))
