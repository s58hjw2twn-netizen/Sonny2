"""Orchestrate localized edit -> verification -> watermarked preview.

No automatic final delivery. All file paths must be in a trusted workspace.
Reference verification and independent review are externally supplied attestations;
this prototype does not authenticate their authors.
"""
from pathlib import Path
from hashlib import sha256
import json
from .locked_compositor import composite_locked
from .precision_release_gate import verify_precision_edit, authorize_release, ReleaseDenied
from .review_preview import make_review_preview

def prepare_case(*, source, replacement, mask, workspace, case_id,
                 reference_id, reference_verified, mask_approved,
                 independent_review):
    if not case_id or not case_id.strip():
        raise ReleaseDenied("Case ID required")
    if not reference_verified or not mask_approved or not independent_review:
        raise ReleaseDenied("Verified reference, approved mask and independent review required")
    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    # Avoid overwriting existing case evidence.
    case = root / case_id
    if not case_id.replace("-", "").replace("_", "").isalnum() or case.exists():
        raise ReleaseDenied("Invalid or already existing case ID")
    case.mkdir()
    candidate = case / "candidate.png"
    try:
        composite_locked(source, replacement, mask, candidate, case / "compositor.json", reference_id)
        verification = verify_precision_edit(
            source, candidate, mask, method="pixel_locked_composite",
            reference_id=reference_id, reference_verified=reference_verified,
            mask_approved=mask_approved, independent_review=independent_review,
            customer_approved=False, audit_file=case / "verification.json")
        preview = make_review_preview(candidate, case / "review_preview.png",
                                      case / "preview_audit.json", case_id=case_id)
        return {"case_dir": str(case), "verification": verification, "preview": preview}
    except Exception:
        # Keep evidence for troubleshooting; do not publish candidate.
        (case / "FAILED").write_text("Case failed; do not release", encoding="utf-8")
        raise

def approve_case(case_dir, *, expected_candidate_sha256, customer_approval_token):
    """Records approval for the exact candidate hash; no delivery or publication."""
    case = Path(case_dir)
    if (case / "FAILED").exists():
        raise ReleaseDenied("Failed case")
    audit = json.loads((case / "verification.json").read_text(encoding="utf-8"))
    actual = sha256((case / "candidate.png").read_bytes()).hexdigest()
    if actual != expected_candidate_sha256 or actual != audit["candidate_sha256"]:
        raise ReleaseDenied("Candidate changed since review")
    if not customer_approval_token or not customer_approval_token.strip():
        raise ReleaseDenied("Explicit approval token required")
    if (case / "approval.json").exists():
        raise ReleaseDenied("Approval already recorded")
    audit["customer_approved"] = True
    audit["status"] = "approved_for_release"
    authorize_release(audit)
    record = {"candidate_sha256": actual, "approval_token": customer_approval_token,
              "status": "approved_for_release", "note": "No automatic delivery"}
    (case / "approval.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record
