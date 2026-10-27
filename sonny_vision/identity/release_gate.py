"""Conservative release decision for identity-sensitive Sonny Vision restorations.

This module does not perform recognition or image enhancement. It combines
independently measured signals and fails closed when any evidence is missing.
"""
from math import isfinite


def restoration_release_gate(geometry_reports, *, identity_scores=None,
                             min_identity_score=0.80, texture_review_passed=False,
                             reference_review_passed=False, owner_approved=False):
    """Return a decision and reasons; all thresholds require dataset calibration.

    Each face must have a geometry report and a corresponding identity score.
    A high similarity score alone cannot establish true identity.
    """
    reasons = []
    reports = list(geometry_reports)
    scores = list(identity_scores) if identity_scores is not None else []
    if not reports:
        reasons.append("missing_face_geometry")
    if len(scores) != len(reports):
        reasons.append("missing_identity_scores")
    if not isinstance(min_identity_score, (int, float)) or not isfinite(min_identity_score) or not 0 <= min_identity_score <= 1:
        raise ValueError("invalid provisional identity threshold")
    for index, report in enumerate(reports):
        if not isinstance(report, dict) or report.get("geometry_pass") is not True:
            reasons.append(f"face_{index}_geometry_failed")
        if index < len(scores):
            score = scores[index]
            if not isinstance(score, (int, float)) or not isfinite(score) or not 0 <= score <= 1 or score < min_identity_score:
                reasons.append(f"face_{index}_identity_unverified")
    if not texture_review_passed:
        reasons.append("texture_review_required")
    if not reference_review_passed:
        reasons.append("reference_review_required")
    if not owner_approved:
        reasons.append("owner_approval_required")
    return {"release_allowed": not reasons, "reasons": reasons,
            "faces_evaluated": len(reports), "threshold_provisional": True}
