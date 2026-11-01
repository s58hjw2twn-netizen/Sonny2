from sonny.rsi_cycle_bridge import evaluate_cycle, evaluate_sequence


def manifest():
    return {"benchmark_id": "frozen-v1", "cases": ["a", "b"],
            "minimum_gain": 0.1, "maximum_regressions": 0,
            "fixture_sha256": "a" * 64}


def cycle(i):
    return evaluate_cycle(i, manifest(), {"a": 0.4, "b": 0.4},
                          {"a": 0.7, "b": 0.7},
                          independent_evidence_id=f"external-{i}",
                          safety_passed=True, heldout_passed=True)


def test_three_cycles_eligible_for_external_audit_only():
    result = evaluate_sequence([cycle(1), cycle(2), cycle(3)])
    assert result["status"] == "READY_FOR_EXTERNAL_EVIDENCE_AUDIT"
    assert result["verified_rsi"] is False


def test_missing_independent_evidence_rejected():
    reports = [cycle(1), cycle(2), evaluate_cycle(
        3, manifest(), {"a": 0.4, "b": 0.4}, {"a": 0.7, "b": 0.7},
        safety_passed=True, heldout_passed=True)]
    assert evaluate_sequence(reports)["status"] == "MISSING_OR_DUPLICATE_EVIDENCE"


def test_mismatched_frozen_fixture_rejected():
    reports = [cycle(1), cycle(2), cycle(3)]
    reports[2]["fixture_sha256"] = "b" * 64
    assert evaluate_sequence(reports)["status"] == "MISMATCHED_FROZEN_BENCHMARK"


def test_failed_candidate_never_promoted():
    result = evaluate_cycle(1, manifest(), {"a": 0.4, "b": 0.4},
                            {"a": 0.4, "b": 0.4})
    assert result["meets_preregistered_thresholds"] is False
    assert result["commit_allowed"] is False
    assert result["promotion_allowed"] is False
