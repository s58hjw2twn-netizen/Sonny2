"""Sonny Vision precision mode: fail-closed, masked, reference-guided edits.

No generative replacement is performed here. Human review of reference accuracy
and identity is mandatory; this module only enforces pixel containment.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from PIL import Image, ImageChops
from .protected_edits import ProtectedEditError, validate_local_edit


@dataclass(frozen=True)
class EditRequest:
    source: str
    reference_patch: str
    mask: str
    output: str
    allowed_regions: tuple
    reference_note: str
    approval_required: bool = True


def _digest(path):
    h = sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def apply_precision_edit(request: EditRequest):
    """Composite patch only where mask is nonzero; reject all other changes.

    Patch and mask must be full-canvas images. Mask must be grayscale with
    values exactly 0 or 255, preventing partially blended edge modifications
    outside the authorized mask. The original file is never overwritten.
    """
    if not request.allowed_regions or not request.reference_note.strip():
        raise ProtectedEditError("Authorized regions and reference provenance required")
    src = Path(request.source).resolve()
    dest = Path(request.output).resolve()
    if src == dest or dest == Path(request.reference_patch).resolve() or dest == Path(request.mask).resolve():
        raise ProtectedEditError("Output must not overwrite any input")
    if dest.exists():
        raise ProtectedEditError("Output exists; refusing overwrite")
    with Image.open(src) as original, Image.open(request.reference_patch) as patch, Image.open(request.mask) as mask:
        if original.size != patch.size or original.size != mask.size:
            raise ProtectedEditError("Source, patch and mask dimensions differ")
        if mask.mode != "L":
            raise ProtectedEditError("Mask must be grayscale L")
        if mask.getextrema()[1] == 0:
            raise ProtectedEditError("Empty edit mask")
        if mask.point(lambda v: 255 if v not in (0, 255) else 0).getbbox():
            raise ProtectedEditError("Mask must be binary 0/255")
        width, height = original.size
        for region in request.allowed_regions:
            if len(region) != 4 or any(type(v) is not int for v in region):
                raise ProtectedEditError("Invalid region")
            l, t, r, b = region
            if not (0 <= l < r <= width and 0 <= t < b <= height):
                raise ProtectedEditError("Out-of-bounds region")
        # Reject mask changes outside the authorized rectangles before writing.
        pixels = mask.load()
        for y in range(height):
            for x in range(width):
                if pixels[x, y] and not any(l <= x < r and t <= y < b for l, t, r, b in request.allowed_regions):
                    raise ProtectedEditError("Mask extends beyond authorized region")
        before_hash = _digest(src)
        result = Image.composite(patch.convert("RGBA"), original.convert("RGBA"), mask)
        if not ImageChops.difference(result, original.convert("RGBA")).getbbox():
            raise ProtectedEditError("Patch made no visible changes")
        # Lossless PNG only: lossy encoders modify pixels outside the mask.
        if dest.suffix.lower() != ".png":
            raise ProtectedEditError("Precision output must be PNG")
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            result.save(dest, format="PNG")
            audit = validate_local_edit(src, dest, request.allowed_regions)
            # Stronger than rectangle check: changed pixels must also lie in mask.
            with Image.open(dest) as saved:
                diff = ImageChops.difference(original.convert("RGBA"), saved.convert("RGBA"))
                for channel in diff.split():
                    outside = ImageChops.multiply(channel, ImageChops.invert(mask))
                    if outside.getbbox():
                        raise ProtectedEditError("Change outside edit mask")
            if _digest(src) != before_hash:
                raise ProtectedEditError("Source modified during edit")
        except Exception:
            dest.unlink(missing_ok=True)
            raise
    return {
        "status": "awaiting_human_approval",
        "source_sha256": before_hash,
        "output_sha256": _digest(dest),
        "changed_pixels": audit["changed_pixels"],
        "reference_note": request.reference_note,
        "historical_accuracy_verified": False,
        "identity_verified": False,
        "customer_approved": False,
    }
