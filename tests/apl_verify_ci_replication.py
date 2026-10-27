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
for name in ("alpha", "beta"):
    directory = root / ("apl-real-" + name)
    manifest = json.loads((directory / "manifest.json").read_text())
    for filename in ("report.json", "ledger.jsonl", "candidate.diff"):
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
                  "github_artifact_manifest_verified": True,
                  "independent_external_custodian_verified": False,
                  "scientific_improvement_proven": False,
                  "unattended_commit_allowed": False,
                  "promotion_allowed": False}, indent=2))
