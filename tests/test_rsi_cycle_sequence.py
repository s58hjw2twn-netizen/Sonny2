from sonny.rsi_cycle_sequence import assess_sequence


def reports():
    return [dict(sequence=i, independent_evidence_id=f"attestation-{i}",
                 safety_passed=True, heldout_passed=True,
                 meets_preregistered_thresholds=True) for i in range(1, 4)]


def test_three_cycles_only_qualify_for_audit():
    result = assess_sequence(reports())
    assert result["status"] == "READY_FOR_EXTERNAL_EVIDENCE_AUDIT"
    assert result["verified_rsi"] is False


def test_two_cycles_insufficient():
    assert assess_sequence(reports()[:2])["status"] == "INSUFFICIENT_CYCLES"


def test_duplicate_evidence_rejected():
    r = reports()
    r[2]["independent_evidence_id"] = r[0]["independent_evidence_id"]
    assert assess_sequence(r)["status"] == "MISSING_OR_DUPLICATE_EVIDENCE"


def test_failed_safety_rejected():
    r = reports()
    r[1]["safety_passed"] = False
    assert assess_sequence(r)["status"] == "SAFETY_OR_HELDOUT_FAILED"
