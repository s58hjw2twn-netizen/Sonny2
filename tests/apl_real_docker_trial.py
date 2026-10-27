"""GitHub-hosted, non-production APL trial. Two separate CI jobs execute this script.
No generated patch is committed, merged, or deployed.
"""
import hashlib
import json
import os
import subprocess
import sys
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
# Patch is a harmless experimental-only comment. The real test is Docker execution,
# not a claim that the patch improved the model.
try:
    target.write_text(original + "\n# isolated Docker trial candidate\n")
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
""")
image = subprocess.check_output(
    ["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}",
     "python:3.11-slim"], text=True).strip()
ledger = out / "ledger.jsonl"
append_lineage(ledger, {"replica_id": os.environ["APL_REPLICA_ID"],
                        "github_run_id": os.environ["GITHUB_RUN_ID"],
                        "github_job": os.environ["GITHUB_JOB"]})
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
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (out / "report.json", ledger, patch)}
(out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2))
print("Docker trial completed with four passing container test executions; no improvement proven")
