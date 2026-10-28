"""Fail-closed constraints for precision-image workflows.

These checks are independent of model-generated explanations.
"""
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import numpy as np


class ConstraintViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class PrecisionRequest:
    preserve_outside_mask: bool
    period_specific_accuracy: bool
    reference_id: str | None = None
    reference_verified: bool = False


def authorize_image_method(request: PrecisionRequest, method: str) -> None:
    """Never use whole-frame synthesis for a protected-region edit."""
    if request.preserve_outside_mask and method != "pixel_locked_composite":
        raise ConstraintViolation("Whole-image generation prohibited for precision edits")
    if request.period_specific_accuracy and (
        not request.reference_id or not request.reference_verified
    ):
        raise ConstraintViolation("Historical accuracy lacks verified period reference")


def verify_outside_mask(source, candidate, mask) -> dict:
    """Compare decoded pixels; reject any difference outside an explicit mask."""
    with Image.open(source) as original, Image.open(candidate) as result, Image.open(mask) as region:
        if original.size != result.size or original.size != region.size:
            raise ConstraintViolation("Image dimensions differ")
        a = np.asarray(original.convert("RGBA"))
        b = np.asarray(result.convert("RGBA"))
        m = np.asarray(region.convert("L")) > 0
    if not np.any(m):
        raise ConstraintViolation("Empty authorized edit mask")
    changed = np.any(a != b, axis=2)
    outside = int(np.count_nonzero(changed & ~m))
    if outside:
        raise ConstraintViolation(f"{outside} unauthorized pixels changed")
    return {"status": "verified_pixel_boundary", "outside_changed_pixels": 0,
            "inside_changed_pixels": int(np.count_nonzero(changed & m)),
            "authorized_pixels": int(np.count_nonzero(m))}


def assert_completion(*, pixel_verified: bool, historical_claim: bool,
                      period_reference_verified: bool, independent_review: bool) -> None:
    if not pixel_verified or not independent_review:
        raise ConstraintViolation("Unverified output cannot be marked complete")
    if historical_claim and not period_reference_verified:
        raise ConstraintViolation("Unsupported historical-accuracy claim")
