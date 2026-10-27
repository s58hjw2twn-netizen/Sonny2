"""Fail-closed, side-effect-free gate for paired RSI research evidence.

No code execution, provider calls, filesystem writes, or promotion occur here.
This gate cannot establish independent verification from caller-supplied scores.
"""
import hashlib
import json
import math


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def assess_experiment(manifest: dict, baseline: dict, candidate: dict) -> dict:
    """Compare preregistered, matched benchmark results; never authorize commits."""
    if not isinstance(manifest, dict) or set(manifest) != {"benchmark_id", "cases", "minimum_gain", "maximum_regressions", "fixture_sha256"}:
        raise ValueError("invalid frozen benchmark manifest")
    cases = manifest["cases"]
    if not isinstance(manifest["benchmark_id"], str) or not manifest["benchmark_id"].strip():
        raise ValueError("benchmark id required")
    if not isinstance(cases, list) or not cases or any(not isinstance(x, str) or not x for x in cases) or len(set(cases)) != len(cases):
        raise ValueError("cases must be unique nonempty identifiers")
    if not isinstance(manifest["fixture_sha256"], str) or len(manifest["fixture_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in manifest["fixture_sha256"]):
        raise ValueError("fixture digest required")
    gain = manifest["minimum_gain"]
    limit = manifest["maximum_regressions"]
    if isinstance(gain, bool) or not isinstance(gain, (float, int)) or not math.isfinite(gain) or gain <= 0:
        raise ValueError("minimum gain must be positive")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("invalid regression limit")
    expected = set(cases)
    for scores in (baseline, candidate):
        if not isinstance(scores, dict) or set(scores) != expected:
            raise ValueError("paired case identifiers do not match frozen manifest")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values()):
            raise ValueError("scores must be finite numbers in [0,1]")
    differences = [candidate[k] - baseline[k] for k in cases]
    observed_gain = sum(differences) / len(differences)
    regressions = [k for k in cases if candidate[k] < baseline[k]]
    eligible = observed_gain >= gain and len(regressions) <= limit
    return {
        "manifest_sha256": _digest(manifest),
        "benchmark_id": manifest["benchmark_id"],
        "fixture_sha256": manifest["fixture_sha256"],
        "sample_size": len(cases),
        "mean_gain": observed_gain,
        "regressions": regressions,
        "meets_preregistered_thresholds": eligible,
        "independently_verified": False,
        "status": "AWAITING_INDEPENDENT_REPLICATION" if eligible else "REJECTED_BY_EVIDENCE_GATE",
        "commit_allowed": False,
        "promotion_allowed": False,
    }
