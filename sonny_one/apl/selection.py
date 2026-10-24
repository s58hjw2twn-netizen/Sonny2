"""Deterministic, bounded offline candidate selection for APL-001.

Selects one *review candidate* from independently scored proposals. This
module does not generate patches, execute code, train models, or promote them.
"""
import math


def select_for_review(candidates, *, max_candidates=10, min_delta=0.08):
    if type(max_candidates) is not int or not 1 <= max_candidates <= 10:
        raise ValueError("Candidate budget must be an integer in [1, 10]")
    if type(min_delta) not in (int, float) or not math.isfinite(min_delta) or not 0 < min_delta <= 1:
        raise ValueError("Invalid improvement threshold")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= max_candidates:
        raise ValueError("Invalid candidate count")
    ids = set()
    eligible = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {"candidate_id", "cycle_assessment"}:
            raise ValueError("Candidate record must contain exact required fields")
        cid, assessment = candidate["candidate_id"], candidate["cycle_assessment"]
        if not isinstance(cid, str) or not cid.strip() or cid in ids:
            raise ValueError("Duplicate or invalid candidate ID")
        ids.add(cid)
        if not isinstance(assessment, dict) or assessment.get("promotion") != "FORBIDDEN":
            raise ValueError("Missing review-only assessment")
        if assessment.get("improvement_proven") is not False or assessment.get("recursive_improvement_proven") is not False:
            raise ValueError("Invalid scientific claim")
        cycles = assessment.get("cycles")
        if (not isinstance(cycles, list) or len(cycles) < 3 or len(cycles) > 20
                or assessment.get("cycle_count") != len(cycles)):
            raise ValueError("Invalid cycle evidence")
        seen = set()
        cycle_candidates = set()
        deltas = []
        for cycle in cycles:
            if not isinstance(cycle, dict):
                raise ValueError("Invalid cycle")
            cycle_candidate = cycle.get("candidate_id")
            if not isinstance(cycle_candidate, str) or not cycle_candidate.strip() or cycle_candidate in cycle_candidates:
                raise ValueError("Duplicate or invalid per-cycle candidate ID")
            cycle_candidates.add(cycle_candidate)
            cycle_id = cycle.get("cycle_id")
            if not isinstance(cycle_id, str) or not cycle_id.strip() or cycle_id in seen:
                raise ValueError("Duplicate or invalid cycle ID")
            seen.add(cycle_id)
            delta = cycle.get("mean_delta")
            interval = cycle.get("bootstrap_95_percentile_interval")
            if (type(delta) not in (int, float) or not math.isfinite(delta)
                    or not isinstance(interval, list) or len(interval) != 2
                    or any(type(x) not in (int, float) or not math.isfinite(x) for x in interval)
                    or not -1 <= interval[0] <= interval[1] <= 1
                    or not -1 <= delta <= 1):
                raise ValueError("Invalid metric evidence")
            expected = delta >= min_delta and interval[0] > 0
            if cycle.get("review_recommended") is not expected:
                raise ValueError("Inconsistent cycle decision")
            deltas.append(delta)
        expected_all = all(cycle["review_recommended"] for cycle in cycles)
        if (assessment.get("all_cycles_positive") is not expected_all
                or assessment.get("human_review_recommended") is not expected_all):
            raise ValueError("Inconsistent assessment decision")
        if expected_all:
            eligible.append((sum(deltas) / len(deltas), cid))
    eligible.sort(key=lambda pair: (-pair[0], pair[1]))
    return {
        "selected_candidate_id": eligible[0][1] if eligible else None,
        "review_candidate_count": len(eligible),
        "selection_basis": "Highest average paired score delta across qualifying cycles; lexical tie break",
        "human_review_required": True,
        "promotion": "FORBIDDEN",
        "improvement_proven": False,
        "recursive_improvement_proven": False,
        "limitations": "Candidate selection only. No external grader authentication, independent holdout custody or causal RSI proof.",
    }


def select_verified_for_review(candidates, *, max_candidates=10, min_delta=0.08,
                               resamples=1000, seed=20261024):
    """Recompute all cycle decisions from raw evidence before ranking.

    The caller supplies raw cycle records and an independently generated
    assessment; this checks agreement but does not authenticate their source.
    """
    from .cycles import assess_cycles
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= max_candidates:
        raise ValueError("Invalid candidate count")
    checked = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {
            "candidate_id", "raw_cycles", "cycle_assessment"
        }:
            raise ValueError("Candidate must include raw cycles and assessment")
        supplied = candidate["cycle_assessment"]
        if not isinstance(supplied, dict):
            raise ValueError("Invalid assessment")
        computed = assess_cycles(candidate["raw_cycles"], min_delta=min_delta,
                                 resamples=resamples, seed=seed)
        # Compare complete results, not just the favorable decision or delta.
        if supplied != computed:
            raise ValueError("Supplied assessment disagrees with raw evidence")
        checked.append({"candidate_id": candidate["candidate_id"],
                        "cycle_assessment": computed})
    result = select_for_review(checked, max_candidates=max_candidates,
                               min_delta=min_delta)
    result["raw_evidence_recomputed"] = True
    result["limitations"] += (
        " Raw records, independent grader and suite custody remain unauthenticated."
    )
    return result


def select_custodied_for_review(candidates, key, *, expected_custodian,
                                max_candidates=10, min_delta=0.08,
                                resamples=1000, seed=20261024):
    """Authenticate each complete raw cycle before recomputing scores.

    Authentication is relative to an independently controlled HMAC key.
    It cannot establish evaluator independence or the truth of the data.
    """
    from .custody import verify_evidence
    if type(max_candidates) is not int or not 1 <= max_candidates <= 10:
        raise ValueError("Candidate budget must be an integer in [1, 10]")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= max_candidates:
        raise ValueError("Invalid candidate count")
    verified = []
    seen_envelopes = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {
            "candidate_id", "raw_cycles", "cycle_assessment", "envelopes"
        }:
            raise ValueError("Complete raw cycles and custody envelopes required")
        cycles = candidate["raw_cycles"]
        envelopes = candidate["envelopes"]
        if (not isinstance(cycles, list) or not isinstance(envelopes, list)
                or not 3 <= len(cycles) <= 20 or len(cycles) != len(envelopes)):
            raise ValueError("Every cycle requires a custody envelope")
        for cycle, envelope in zip(cycles, envelopes):
            if not verify_evidence(cycle, envelope, key,
                                   expected_custodian=expected_custodian):
                raise ValueError("Cycle custody verification failed")
            digest = envelope["payload_sha256"]
            if digest in seen_envelopes:
                raise ValueError("Replayed custody envelope")
            seen_envelopes.add(digest)
        verified.append({
            "candidate_id": candidate["candidate_id"],
            "raw_cycles": cycles,
            "cycle_assessment": candidate["cycle_assessment"],
        })
    result = select_verified_for_review(
        verified, max_candidates=max_candidates, min_delta=min_delta,
        resamples=resamples, seed=seed)
    result["custody_envelopes_verified"] = True
    result["limitations"] += (
        " HMAC verification assumes independent key custody; it does not "
        "prove score truth, evaluator independence or scientific RSI."
    )
    return result
