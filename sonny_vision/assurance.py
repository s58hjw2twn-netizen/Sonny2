"""Sonny ONE assurance gates: explicit constraints, independent evidence and failure learning.

No self-reported success is accepted as verification. Persisted records contain
technical failure codes, not customer images or personal details.
"""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path


class AssuranceError(ValueError):
    pass


@dataclass(frozen=True)
class Constraint:
    name: str
    required: bool = True


@dataclass(frozen=True)
class Evidence:
    check: str
    passed: bool
    verifier: str
    reference: str


@dataclass
class AssuranceDecision:
    status: str
    failures: list = field(default_factory=list)
    missing: list = field(default_factory=list)


def evaluate(constraints, evidence, *, creator):
    """Fail closed on missing evidence, failed checks, or self-verification."""
    names = [c.name for c in constraints]
    if not names or len(names) != len(set(names)):
        raise AssuranceError("Unique constraints required")
    observed = {}
    for item in evidence:
        if item.check not in names:
            raise AssuranceError("Unexpected check")
        if item.check in observed:
            raise AssuranceError("Duplicate evidence")
        if not item.verifier or item.verifier == creator or not item.reference:
            raise AssuranceError("Independent verifier and traceable reference required")
        observed[item.check] = item
    missing = [c.name for c in constraints if c.required and c.name not in observed]
    failures = [c.name for c in constraints if c.required and c.name in observed and not observed[c.name].passed]
    return AssuranceDecision("rejected" if failures else "unverified" if missing else "verified",
                             failures, missing)


class FailureLedger:
    """Append-only hash-chained JSONL log; validates chain before appending."""
    def __init__(self, path):
        self.path = Path(path)

    def read(self):
        entries = []
        previous = "0" * 64
        if not self.path.exists():
            return entries
        for line in self.path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if entry.get("previous_hash") != previous:
                raise AssuranceError("Broken failure ledger chain")
            payload = {k: v for k, v in entry.items() if k != "hash"}
            expected = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if entry.get("hash") != expected:
                raise AssuranceError("Tampered failure ledger")
            previous = expected
            entries.append(entry)
        return entries

    def record(self, *, task_type, method, failure_code, evidence_ref):
        if not all((task_type, method, failure_code, evidence_ref)):
            raise AssuranceError("Failure fields required")
        entries = self.read()
        payload = {"task_type": task_type, "method": method,
                   "failure_code": failure_code, "evidence_ref": evidence_ref,
                   "previous_hash": entries[-1]["hash"] if entries else "0" * 64}
        payload["hash"] = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(payload, sort_keys=True) + "\n")
        return payload

    def blocked_methods(self, task_type, *, threshold=2):
        if threshold < 1:
            raise AssuranceError("Invalid failure threshold")
        counts = {}
        for entry in self.read():
            if entry["task_type"] == task_type:
                key = entry["method"]
                counts[key] = counts.get(key, 0) + 1
        return {method for method, count in counts.items() if count >= threshold}


def choose_method(task_type, candidates, ledger):
    blocked = ledger.blocked_methods(task_type)
    for method in candidates:
        if method not in blocked:
            return method
    raise AssuranceError("No eligible method: escalate to human review")
