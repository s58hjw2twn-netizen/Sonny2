"""Conservative, model-free Sonny Vision research checks.

These metrics are heuristics, not biometric identity verification or release approval.
"""
from __future__ import annotations

import cv2
import numpy as np

from sonny_vision.archival_engine import _validate, quality_gate


def _mask(mask: np.ndarray | None, shape: tuple[int, int], name: str) -> np.ndarray:
    if mask is None or mask.shape != shape or mask.dtype != np.bool_ or not np.any(mask):
        raise ValueError(f"{name} requires a nonempty boolean HxW mask")
    return mask


def evaluate_preservation(source: np.ndarray, candidate: np.ndarray,
                          face_mask: np.ndarray | None,
                          historical_mask: np.ndarray | None = None) -> dict:
    """Fail closed on missing face mask; historic details must be reviewed separately."""
    _validate(source)
    _validate(candidate)
    if source.shape != candidate.shape:
        raise ValueError("Candidate dimensions differ")
    face = _mask(face_mask, source.shape[:2], "face_mask")
    diff = np.abs(source.astype(np.int16) - candidate.astype(np.int16))
    base = quality_gate(source, candidate, face)
    face_delta = diff[face]
    result = {
        "face_max_channel_change": int(face_delta.max()),
        "face_mean_channel_change": float(face_delta.mean()),
        "face_changed_fraction_over_16": float(np.mean(np.any(diff[face] > 16, axis=1))),
        "face_heuristic_passed": bool(base["passed"]),
        "identity_verified": False,
        "landmarks_verified": False,
        "historical_details_verified": False,
        "release_allowed": False,
        "manual_review_required": True,
        "confidence": None,
        "limitations": "Pixel differences cannot prove identity, age, or authentic texture.",
    }
    if historical_mask is not None:
        historic = _mask(historical_mask, source.shape[:2], "historical_mask")
        result["historical_max_channel_change"] = int(diff[historic].max())
        result["historical_mean_channel_change"] = float(diff[historic].mean())
    return result


def detect_damage_candidates(image: np.ndarray, *, threshold: int = 28) -> np.ndarray:
    """Conservative thin dark-mark candidate mask; NOT confirmed scratch detection."""
    _validate(image)
    if type(threshold) is not int or not 1 <= threshold <= 255:
        raise ValueError("threshold must be integer in 1..255")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return (background.astype(np.int16) - gray.astype(np.int16)) >= threshold


def selective_conventional_repair(image: np.ndarray, damage_mask: np.ndarray,
                                  protected_mask: np.ndarray) -> np.ndarray:
    """Inpaint only reviewed non-protected damage pixels; input remains unchanged."""
    _validate(image)
    damage = _mask(damage_mask, image.shape[:2], "damage_mask")
    protected = _mask(protected_mask, image.shape[:2], "protected_mask")
    permitted = damage & ~protected
    if not np.any(permitted):
        return image.copy()
    repaired = cv2.inpaint(image, permitted.astype(np.uint8) * 255, 2, cv2.INPAINT_TELEA)
    output = image.copy()
    output[permitted] = repaired[permitted]
    return output


def texture_diagnostics(source: np.ndarray, candidate: np.ndarray,
                        face_mask: np.ndarray) -> dict:
    """Gradient-energy proxy only; does not identify genuine or hallucinated pores."""
    _validate(source)
    _validate(candidate)
    if source.shape != candidate.shape:
        raise ValueError("Candidate dimensions differ")
    face = _mask(face_mask, source.shape[:2], "face_mask")
    def energy(image: np.ndarray) -> float:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        dx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
        dy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
        return float(np.mean((dx[face] ** 2 + dy[face] ** 2)))
    before, after = energy(source), energy(candidate)
    return {"source_gradient_energy": before, "candidate_gradient_energy": after,
            "energy_ratio": after / before if before > 0 else None,
            "authentic_texture_verified": False, "manual_review_required": True}
