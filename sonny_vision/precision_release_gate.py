"""Fail-closed approval and pixel integrity checks for localized restoration."""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
from PIL import Image

class ReleaseDenied(RuntimeError):
    pass

def verify_precision_edit(source, candidate, mask, *, method, reference_id,
                          reference_verified=False, mask_approved=False,
                          independent_review=None, customer_approved=False,
                          audit_file=None, max_mask_fraction=0.02):
    if method != "pixel_locked_composite":
        raise ReleaseDenied("Full-image or unknown editing methods prohibited")
    if not reference_id or not reference_verified:
        raise ReleaseDenied("Verified reference required")
    if not mask_approved:
        raise ReleaseDenied("Approved mask required")
    a = np.asarray(Image.open(source).convert("RGB"))
    b = np.asarray(Image.open(candidate).convert("RGB"))
    m = np.asarray(Image.open(mask).convert("L"))
    if a.shape != b.shape or m.shape != a.shape[:2]:
        raise ReleaseDenied("Dimension mismatch")
    allowed = m > 0
    if not allowed.any() or allowed.mean() > max_mask_fraction:
        raise ReleaseDenied("Empty or oversized mask")
    changed = np.any(a != b, axis=2)
    outside = int(np.count_nonzero(changed & ~allowed))
    if outside:
        raise ReleaseDenied("Pixels changed outside authorized mask")
    if not independent_review:
        raise ReleaseDenied("Independent accuracy and blend review required")
    def digest(p):
        return sha256(Path(p).read_bytes()).hexdigest()
    audit = {
        "source_sha256": digest(source),
        "candidate_sha256": digest(candidate),
        "mask_sha256": digest(mask),
        "reference_id": reference_id,
        "reference_verified": True,
        "independent_review": independent_review,
        "changed_pixels": int(changed.sum()),
        "outside_mask_changes": outside,
        "customer_approved": bool(customer_approved),
        "status": "approved_for_release" if customer_approved else "awaiting_customer_approval"
    }
    if audit_file:
        Path(audit_file).write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit

def authorize_release(audit):
    if audit.get("status") != "approved_for_release":
        raise ReleaseDenied("Explicit customer approval required")
    return True
