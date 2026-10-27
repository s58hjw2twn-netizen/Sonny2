"""Conservative Sonny Vision archival restoration primitives.

No generative synthesis, face replacement, or external model downloads.
Input remains immutable; every output requires human approval.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json

import cv2
import numpy as np


@dataclass(frozen=True)
class Analysis:
    blur_variance: float
    contrast_std: float
    clipping_fraction: float
    noise_estimate: float


def analyze(image: np.ndarray) -> Analysis:
    _validate(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    smooth = cv2.GaussianBlur(gray, (3, 3), 0)
    return Analysis(
        blur_variance=float(lap.var()),
        contrast_std=float(gray.std()),
        clipping_fraction=float(np.mean((gray <= 3) | (gray >= 252))),
        noise_estimate=float(np.median(np.abs(gray.astype(np.float32) - smooth.astype(np.float32)))),
    )


def _validate(image: np.ndarray) -> None:
    if image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected uint8 BGR image with three channels")
    if min(image.shape[:2]) < 16:
        raise ValueError("Image is too small")


def restore_archival(image: np.ndarray, clip_limit: float = 1.4) -> np.ndarray:
    """Bounded luminance-only CLAHE; does not synthesize missing details."""
    _validate(image)
    if not 1.0 <= clip_limit <= 2.0:
        raise ValueError("clip_limit must be between 1 and 2")
    lab = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(12, 12))
    enhanced = clahe.apply(lab[:, :, 0])
    lab[:, :, 0] = cv2.addWeighted(lab[:, :, 0], 0.65, enhanced, 0.35, 0)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def quality_gate(source: np.ndarray, candidate: np.ndarray, protected_mask: np.ndarray | None = None,
                 max_protected_change: int = 16, max_clipping_increase: float = 0.02) -> dict:
    """Conservative heuristic gate, NOT an independent identity verification."""
    _validate(source)
    _validate(candidate)
    if source.shape != candidate.shape:
        raise ValueError("Candidate dimensions differ")
    if protected_mask is None:
        return {"passed": False, "reason": "missing independently reviewed protected-region mask",
                "identity_verified": False, "release_allowed": False}
    if protected_mask.shape != source.shape[:2] or protected_mask.dtype != np.bool_:
        raise ValueError("protected_mask must be a boolean HxW array")
    if not np.any(protected_mask):
        return {"passed": False, "reason": "empty protected mask",
                "identity_verified": False, "release_allowed": False}
    diff = np.abs(source.astype(np.int16) - candidate.astype(np.int16))
    protected_max = int(diff[protected_mask].max())
    old_clip = analyze(source).clipping_fraction
    new_clip = analyze(candidate).clipping_fraction
    passed = protected_max <= max_protected_change and new_clip - old_clip <= max_clipping_increase
    return {"passed": bool(passed), "protected_max_channel_change": protected_max,
            "clipping_increase": round(new_clip - old_clip, 6),
            "identity_verified": False, "release_allowed": False,
            "reason": "heuristic checks only; manual identity and artifact review required"}


def process_file(source_path: str, output_path: str, audit_path: str) -> dict:
    src = Path(source_path)
    original_bytes = src.read_bytes()
    image = cv2.imdecode(np.frombuffer(original_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    _validate(image)
    restored = restore_archival(image)
    ok, png = cv2.imencode(".png", restored)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    output = Path(output_path)
    audit = Path(audit_path)
    if len({src.resolve(), output.resolve(), audit.resolve()}) != 3:
        raise ValueError("Source, output and audit must have distinct paths")
    if src.is_symlink() or output.is_symlink() or audit.is_symlink():
        raise ValueError("Symlink paths are not allowed")
    if output.exists() or audit.exists():
        raise FileExistsError("Existing restoration or audit file")
    with output.open("xb") as handle:
        handle.write(png.tobytes())
    report = {"source_sha256": sha256(original_bytes).hexdigest(),
              "output_sha256": sha256(output.read_bytes()).hexdigest(),
              "analysis": analyze(image).__dict__,
              "quality_gate_passed": False,
              "identity_verified": False, "release_allowed": False,
              "manual_review_required": True,
              "algorithm": "bounded luminance CLAHE; no generative synthesis"}
    with audit.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2))
    return report
