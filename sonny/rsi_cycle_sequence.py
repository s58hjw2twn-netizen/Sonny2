"""Conservative research-cycle summary. This does not authenticate evidence."""
def assess_sequence(reports):
    if not isinstance(reports, list) or len(reports) < 3:
        return {"status": "INSUFFICIENT_CYCLES", "verified_rsi": False}
    ids = set()
    for index, report in enumerate(reports, 1):
        if not isinstance(report, dict):
            return {"status": "INVALID_REPORT", "verified_rsi": False}
        if report.get("sequence") != index:
            return {"status": "NONCONSECUTIVE", "verified_rsi": False}
        evidence_id = report.get("independent_evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip() or evidence_id in ids:
            return {"status": "MISSING_OR_DUPLICATE_EVIDENCE", "verified_rsi": False}
        ids.add(evidence_id)
        if report.get("safety_passed") is not True or report.get("heldout_passed") is not True:
            return {"status": "SAFETY_OR_HELDOUT_FAILED", "verified_rsi": False}
        if report.get("meets_preregistered_thresholds") is not True:
            return {"status": "NO_VERIFIED_GAIN", "verified_rsi": False}
    return {"status": "READY_FOR_EXTERNAL_EVIDENCE_AUDIT",
            "verified_rsi": False, "cycles": len(reports)}
