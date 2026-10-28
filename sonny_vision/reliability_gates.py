"""Shared Sonny ONE reliability gates for images, business actions and code patches.

These checks enforce declared constraints and evidence; they do not independently
establish the truth of a supplied historical reference or human review.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json

from sonny_vision.assurance import AssuranceError, Constraint, Evidence, evaluate


@dataclass(frozen=True)
class Source:
    identifier: str
    authority: str
    version: str
    retrieved_at: str
    supports: tuple


@dataclass(frozen=True)
class ChangePlan:
    original_sha256: str
    authorized_paths: tuple
    prohibited_paths: tuple
    checks: tuple


def fingerprint(path):
    digest = sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_change_plan(plan, changed_paths, original_path):
    """Preservation-first: reject undeclared or explicitly prohibited paths."""
    if not plan.authorized_paths or not plan.checks:
        raise AssuranceError("Authorization and acceptance checks required")
    if fingerprint(original_path) != plan.original_sha256:
        raise AssuranceError("Original source fingerprint mismatch")
    authorized = set(plan.authorized_paths)
    prohibited = set(plan.prohibited_paths)
    if authorized & prohibited:
        raise AssuranceError("Conflicting authorization")
    if any(p not in authorized or p in prohibited for p in changed_paths):
        raise AssuranceError("Unauthorized change")
    return True


def validate_sources(required_claims, sources):
    """Only explicit claim-to-source mappings count; no inferred coverage."""
    if not required_claims:
        raise AssuranceError("Required claims missing")
    coverage = {claim: [] for claim in required_claims}
    for source in sources:
        if not all((source.identifier, source.authority, source.version, source.retrieved_at)):
            raise AssuranceError("Incomplete provenance")
        for claim in source.supports:
            if claim in coverage:
                coverage[claim].append(source.identifier)
    missing = [claim for claim, references in coverage.items() if not references]
    return {"status": "unverified" if missing else "documented",
            "missing": missing, "coverage": coverage}


def acceptance_gate(plan, evidence, *, creator, customer_approved=False):
    """Never release if a required check is failed, missing, or unapproved."""
    checks = [Constraint(name) for name in plan.checks]
    result = evaluate(checks, evidence, creator=creator)
    if result.status != "verified":
        return {"status": result.status, "failures": result.failures, "missing": result.missing}
    return {"status": "approved" if customer_approved else "awaiting_customer_approval",
            "failures": [], "missing": []}


def compare_frozen_benchmark(baseline, candidate, frozen_manifest):
    """Compare matching frozen case IDs; require no regression on any case."""
    ids = tuple(frozen_manifest)
    if not ids or len(ids) != len(set(ids)):
        raise AssuranceError("Invalid frozen benchmark manifest")
    if set(baseline) != set(ids) or set(candidate) != set(ids):
        raise AssuranceError("Incomplete or mismatched benchmark cases")
    for case in ids:
        if type(baseline[case]) not in (int, float) or type(candidate[case]) not in (int, float):
            raise AssuranceError("Scores must be numeric")
        if not (0 <= baseline[case] <= 1 and 0 <= candidate[case] <= 1):
            raise AssuranceError("Scores must be between zero and one")
    regressions = [case for case in ids if candidate[case] < baseline[case]]
    gains = [case for case in ids if candidate[case] > baseline[case]]
    return {"status": "rejected" if regressions or not gains else "candidate_improved",
            "regressions": regressions, "improved_cases": gains,
            "baseline_mean": sum(baseline.values()) / len(ids),
            "candidate_mean": sum(candidate.values()) / len(ids)}


def recovery_decision(task_type, candidates, ledger):
    """Require human escalation when all methods are blocked; no silent retries."""
    blocked = ledger.blocked_methods(task_type)
    eligible = [method for method in candidates if method not in blocked]
    if not eligible:
        return {"status": "escalate", "method": None}
    return {"status": "retry_requires_new_verification", "method": eligible[0]}
