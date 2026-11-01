"""Bridge a frozen paired benchmark into the conservative RSI cycle ledger.

This module does not run experiments, authenticate attestations, or authorize
writes. A caller must independently obtain trusted evidence before audit.
"""
from .rsi_evidence_gate import assess_experiment
from .rsi_cycle_sequence import assess_sequence


def evaluate_cycle(sequence, manifest, baseline, candidate,
                   independent_evidence_id=None,
                   safety_passed=False, heldout_passed=False):
    if type(sequence) is not int or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    result = assess_experiment(manifest, baseline, candidate)
    return {
        "sequence": sequence,
        "benchmark_id": result["benchmark_id"],
        "manifest_sha256": result["manifest_sha256"],
        "fixture_sha256": result["fixture_sha256"],
        "mean_gain": result["mean_gain"],
        "meets_preregistered_thresholds": result["meets_preregistered_thresholds"],
        "independent_evidence_id": independent_evidence_id,
        "safety_passed": safety_passed is True,
        "heldout_passed": heldout_passed is True,
        "independently_verified": False,
        "commit_allowed": False,
        "promotion_allowed": False,
    }


def evaluate_sequence(reports):
    """Reject cross-benchmark or cross-fixture comparisons before sequence gate."""
    if not isinstance(reports, list) or not reports:
        return assess_sequence(reports)
    if any(not isinstance(report, dict) for report in reports):
        return {"status": "INVALID_REPORT", "verified_rsi": False}
    for field in ("benchmark_id", "manifest_sha256", "fixture_sha256"):
        values = [report.get(field) for report in reports]
        if any(not isinstance(value, str) or not value for value in values) or len(set(values)) != 1:
            return {"status": "MISMATCHED_FROZEN_BENCHMARK", "verified_rsi": False}
    return assess_sequence(reports)
