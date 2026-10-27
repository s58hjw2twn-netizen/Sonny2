"""Conservative translation search on aligned-size grayscale grids.

This measures pixel similarity, not identity. Reject ambiguous or low-texture
matches; never use the result as authorization to release a restoration.
"""
from math import isfinite
from sonny_vision.quality.face_regions import crop_region


def estimate_translation(original, restored, box, *, max_shift=3, ambiguity_margin=0.005):
    if type(max_shift) is not int or max_shift < 0 or max_shift > 32:
        raise ValueError("invalid search radius")
    if type(ambiguity_margin) not in (int, float) or not isfinite(ambiguity_margin) or ambiguity_margin < 0:
        raise ValueError("invalid ambiguity margin")
    reference = crop_region(original, box)
    if any(type(v) not in (float, int) or not isfinite(v) or not 0 <= v <= 1
           for row in reference for v in row):
        raise ValueError("invalid reference pixels")
    flat = [v for row in reference for v in row]
    if max(flat) - min(flat) < 0.05:
        return {"accepted": False, "reason": "low_texture", "dx": None, "dy": None}
    candidates = []
    left, top, right, bottom = box
    for dy in range(-max_shift, max_shift + 1):
        for dx in range(-max_shift, max_shift + 1):
            try:
                crop = crop_region(restored, (left + dx, top + dy, right + dx, bottom + dy))
            except ValueError:
                continue
            if any(type(v) not in (float, int) or not isfinite(v) or not 0 <= v <= 1
                   for row in crop for v in row):
                raise ValueError("invalid candidate pixels")
            error = sum(abs(a-b) for row_a, row_b in zip(reference, crop)
                        for a, b in zip(row_a, row_b)) / len(flat)
            candidates.append((error, dx, dy))
    if not candidates:
        return {"accepted": False, "reason": "no_valid_candidates", "dx": None, "dy": None}
    candidates.sort()
    best = candidates[0]
    if len(candidates) > 1 and candidates[1][0] - best[0] <= ambiguity_margin:
        return {"accepted": False, "reason": "ambiguous_match", "dx": None, "dy": None}
    return {"accepted": True, "reason": "unique_pixel_match", "dx": best[1],
            "dy": best[2], "mean_absolute_error": best[0],
            "identity_verified": False, "alignment_verified": False}
