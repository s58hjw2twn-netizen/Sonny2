"""Fail-closed mask-limited photo compositor for Sonny Vision."""
from pathlib import Path
from PIL import Image
import numpy as np
import hashlib
import json

def composite_locked(original, replacement, mask, output, audit_path, reference_id):
    if not reference_id or not str(reference_id).strip():
        raise ValueError("Reference identifier required")
    src = Image.open(original).convert("RGB")
    edit = Image.open(replacement).convert("RGB")
    gate = Image.open(mask).convert("L")
    if src.size != edit.size or src.size != gate.size:
        raise ValueError("All images must have identical dimensions")
    a = np.asarray(src).copy()
    b = np.asarray(edit)
    m = np.asarray(gate)
    if not np.any(m):
        raise ValueError("Empty edit mask")
    a[m > 0] = b[m > 0]
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a, "RGB").save(out, format="PNG")
    check = np.asarray(Image.open(out).convert("RGB"))
    original_pixels = np.asarray(src)
    outside_changes = int(np.count_nonzero(np.any(
        check[m == 0] != original_pixels[m == 0], axis=1)))
    if outside_changes:
        out.unlink(missing_ok=True)
        raise RuntimeError("FAIL: pixels outside edit mask changed")
    evidence = {
        "source_sha256": hashlib.sha256(Path(original).read_bytes()).hexdigest(),
        "result_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "reference_id": str(reference_id),
        "authorized_pixels": int(np.count_nonzero(m)),
        "outside_changed_pixels": outside_changes,
        "status": "pixel_preservation_passed",
        "historical_accuracy_verified": False,
        "human_approval": False
    }
    Path(audit_path).write_text(json.dumps(evidence, indent=2))
    return evidence
