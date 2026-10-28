"""Conservative release decision for identity-sensitive Sonny Vision restorations.

No score proves identity. Every required review must be explicitly approved.
"""
from math import isfinite


def _score(value):
    return type(value) in (int, float) and isfinite(value) and 0 <= value <= 1


def restoration_release_gate(geometry_reports, *, identity_scores=None,
                             min_identity_score=0.80, texture_review_passed=False,
                             reference_review_passed=False, owner_approved=False):
    """Fail closed on incomplete evidence; all thresholds are provisional."""
    if not _score(min_identity_score):
        raise ValueError("invalid provisional identity threshold")
    reasons = []
    reports = list(geometry_reports)
    scores = list(identity_scores) if identity_scores is not None else []
    if not reports:
        reasons.append("missing_face_geometry")
    if len(scores) != len(reports):
        reasons.append("missing_identity_scores")
    for index, report in enumerate(reports):
        if not isinstance(report, dict) or report.get("geometry_pass") is not True:
            reasons.append(f"face_{index}_geometry_failed")
        if index < len(scores):
            score = scores[index]
            if not _score(score) or score < min_identity_score:
                reasons.append(f"face_{index}_identity_unverified")
    if texture_review_passed is not True:
        reasons.append("texture_review_required")
    if reference_review_passed is not True:
        reasons.append("reference_review_required")
    if owner_approved is not True:
        reasons.append("owner_approval_required")
    return {"release_allowed": not reasons, "reasons": reasons,
            "faces_evaluated": len(reports), "threshold_provisional": True}
