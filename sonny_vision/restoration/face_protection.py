"""Fail-closed face-region mask geometry, without third-party dependencies.

All bounding boxes use normalized (left, top, right, bottom) coordinates.
Masks protect the entire bounding rectangle, with optional proportional padding.
For multi-person photographs, pass every detected face box. A caller must not
interpret an empty list as evidence that no face exists.
"""
from __future__ import annotations

from math import isfinite
from typing import Iterable, Sequence


def protected_boxes(
    faces: Iterable[Sequence[float]],
    *,
    padding: float = 0.12,
    require_faces: bool = True,
) -> list[tuple[float, float, float, float]]:
    if not isfinite(padding) or not 0 <= padding <= 1:
        raise ValueError("padding must be finite and between zero and one")
    boxes = []
    for face in faces:
        if len(face) != 4:
            raise ValueError("face box must have four coordinates")
        l, t, r, b = map(float, face)
        if not all(isfinite(v) and 0 <= v <= 1 for v in (l, t, r, b)):
            raise ValueError("invalid normalized face box")
        if not (l < r and t < b):
            raise ValueError("face box must have positive area")
        dx, dy = (r - l) * padding, (b - t) * padding
        boxes.append((max(0.0, l - dx), max(0.0, t - dy),
                      min(1.0, r + dx), min(1.0, b + dy)))
    if require_faces and not boxes:
        raise ValueError("no verified face boxes: cannot safely apply scene-only AI")
    return boxes


def is_protected(x: float, y: float, boxes: Iterable[Sequence[float]]) -> bool:
    """Test whether a normalized image coordinate falls in a protected box."""
    if not all(isfinite(v) and 0 <= v <= 1 for v in (x, y)):
        raise ValueError("invalid normalized coordinate")
    return any(l <= x <= r and t <= y <= b for l, t, r, b in boxes)
