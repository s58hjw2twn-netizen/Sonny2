"""Conservative, dependency-free geometry checks for Sonny Vision.

Coordinates must be normalized to [0, 1] in the same aligned face crop.
This gate does not establish identity; embedding/reference checks are required
before any commercial acceptance decision.
"""
from __future__ import annotations

from math import hypot, isfinite
from typing import Mapping, Sequence

REQUIRED = ("left_eye", "right_eye", "nose", "mouth_left", "mouth_right", "chin")


def _point(value: Sequence[float]) -> tuple[float, float]:
    if len(value) != 2:
        raise ValueError("landmarks must be two-dimensional")
    x, y = float(value[0]), float(value[1])
    if not (isfinite(x) and isfinite(y) and 0 <= x <= 1 and 0 <= y <= 1):
        raise ValueError("landmarks must be finite normalized coordinates")
    return x, y


def geometry_report(
    original: Mapping[str, Sequence[float]],
    restored: Mapping[str, Sequence[float]],
    *,
    max_mean_displacement: float = 0.015,
    max_single_displacement: float = 0.035,
) -> dict:
    """Return a fail-closed facial landmark displacement report.

    Thresholds are provisional engineering defaults, not validated identity
    acceptance criteria. Both inputs must use identical crop registration.
    """
    if not (0 <= max_mean_displacement <= 1 and 0 <= max_single_displacement <= 1):
        raise ValueError("invalid thresholds")
    if any(k not in original or k not in restored for k in REQUIRED):
        raise ValueError("missing required facial landmarks")
    distances = {}
    for key in REQUIRED:
        a, b = _point(original[key]), _point(restored[key])
        distances[key] = hypot(a[0] - b[0], a[1] - b[1])
    mean = sum(distances.values()) / len(distances)
    maximum = max(distances.values())
    passed = mean <= max_mean_displacement and maximum <= max_single_displacement
    return {
        "geometry_pass": passed,
        "mean_displacement": round(mean, 6),
        "max_displacement": round(maximum, 6),
        "per_landmark": {k: round(v, 6) for k, v in distances.items()},
        "identity_verified": False,
        "requires_reference_review": True,
    }
