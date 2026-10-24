"""Read-only adapter: completed APL candidate evaluations -> causal predictions.

This uses the existing APL calibration validator. It measures prediction of
human-review eligibility, NOT improvement, intelligence, or consciousness.
Input provenance and independent custody must be verified separately.
"""
from __future__ import annotations

from sonny_one.apl.calibration import prediction_calibration
from sonny_one.causal_self_model import CausalSelfModel


def apl_self_prediction_report(records: list[dict]) -> dict:
    # Validate every record and all suite exit codes before constructing a model.
    summary = prediction_calibration(records)
    model = CausalSelfModel({"apl_review_eligibility": True})
    for record in records:
        cid = record["candidate_id"]
        report = record["report"]
        success = report["status"] == "ELIGIBLE_FOR_HUMAN_REVIEW"
        model.predict(cid, "apl_review_eligibility", record["predicted_pass"],
                      "Preregistered candidate eligibility prediction")
        model.observe(cid, success, "apl-report:" + cid)
    result = model.report()
    if abs(result["brier_score"] - summary["brier_score"]) > 1e-12:
        raise AssertionError("APL and self-model calibration disagree")
    return {
        "apl_calibration": summary,
        "self_model": result,
        "source": "externally_supplied_apl_records",
        "provenance_verified": False,
        "improvement_proven": False,
        "changes_applied": False,
    }
