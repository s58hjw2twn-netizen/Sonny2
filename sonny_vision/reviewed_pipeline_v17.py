"""V17 orchestration: compute quality checks instead of trusting caller-supplied flags.

A reviewed protection mask is mandatory. Identity review remains an explicit
human assertion, not a computer-vision claim. This module does not grant roles.
"""
from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np
from .archival_engine import quality_gate
from .review_gate_v17 import ReviewDecision, verify_decision\nimport hashlib
from .release_export import export_reviewed


def _decode(path: str) -> np.ndarray:
    raw = np.frombuffer(Path(path).read_bytes(), dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Not a supported image")
    return image


def release_with_quality_review(source_path: str, candidate_path: str,
                                destination_path: str, protected_mask: np.ndarray,
                                decision: ReviewDecision | None, secret: bytes,
                                identity_reviewed: bool = False) -> dict:
    source = _decode(source_path)
    candidate = _decode(candidate_path)
    gate = quality_gate(source, candidate, protected_mask)
    if not gate["passed"]:
        return {"exported": False, "quality": gate, "reason": "quality gate failed"}
    if not identity_reviewed:
        return {"exported": False, "quality": gate, "reason": "human identity review required"}
    exported = export_reviewed(source_path, candidate_path, destination_path,
                               decision, secret, quality_passed=True,
                               identity_reviewed=True)
    return {"exported": exported, "quality": gate,
            "reason": "signed review accepted" if exported else "signed release review missing or invalid"}
