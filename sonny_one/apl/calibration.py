"""Descriptive self-prediction calibration for externally supplied APL outcomes.

Inputs are independently checked completed evaluation reports. No RSI claims.
"""
import math


def prediction_calibration(records):
    """Brier score and prediction bias for completed, valid candidate experiments."""
    if not isinstance(records, list) or not records:
        raise ValueError("Nonempty experiment records required")
    squares = []
    errors = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid experiment record")
        cid = record.get("candidate_id")
        probability = record.get("predicted_pass")
        report = record.get("report")
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("Candidate identifiers must be unique and nonempty")
        seen.add(cid)
        if type(probability) not in (int, float) or not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("Invalid prediction")
        if not isinstance(report, dict) or report.get("candidate_id") != cid:
            raise ValueError("Report identity mismatch")
        if report.get("error") or report.get("status") not in ("REJECTED", "ELIGIBLE_FOR_HUMAN_REVIEW"):
            raise ValueError("No valid completed outcome")
        required = ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout")
        if any(not isinstance(report.get(k), dict)
               or type(report[k].get("exit_code")) is not int
               or report[k]["exit_code"] not in (0, 1)
               or report[k].get("error") or report[k].get("skipped")
               for k in required):
            raise ValueError("Incomplete or infrastructure-failed evaluation")
        # This predicts review eligibility, not functionality or intelligence.
        eligible = all(report[k]["exit_code"] == 0 for k in required)
        if (report["status"] == "ELIGIBLE_FOR_HUMAN_REVIEW") != eligible:
            raise ValueError("Report status conflicts with suite outcomes")
        outcome = int(eligible)
        squares.append((probability - outcome) ** 2)
        errors.append(probability - outcome)
    return {"evaluated_candidates": len(records),
            "brier_score": sum(squares) / len(squares),
            "mean_prediction_bias": sum(errors) / len(errors),
            "target": "Eligibility for human review (not task improvement)",
            "improvement_proven": False,
            "promotion": "FORBIDDEN"}
