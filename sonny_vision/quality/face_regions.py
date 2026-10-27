"""Conservative manually specified face-region extraction.

Boxes use integer pixel coordinates (left, top, right, bottom). No detection
or registration is inferred; callers must provide matching aligned regions.
"""
from sonny_vision.quality.photo_adapter import load_grayscale
from sonny_vision.quality.texture import texture_report


def crop_region(pixels, box):
    if not pixels or not pixels[0] or any(len(row) != len(pixels[0]) for row in pixels):
        raise ValueError("invalid image grid")
    if not isinstance(box, (list, tuple)) or len(box) != 4 or any(type(v) is not int for v in box):
        raise ValueError("box requires four integer coordinates")
    left, top, right, bottom = box
    if not (0 <= left < right <= len(pixels[0]) and 0 <= top < bottom <= len(pixels)):
        raise ValueError("box outside image")
    if right - left < 2 or bottom - top < 2:
        raise ValueError("face region too small")
    return [row[left:right] for row in pixels[top:bottom]]


def compare_manual_regions(original_path, restored_path, original_box, restored_box):
    original = crop_region(load_grayscale(original_path), original_box)
    restored = crop_region(load_grayscale(restored_path), restored_box)
    if len(original) != len(restored) or len(original[0]) != len(restored[0]):
        raise ValueError("face regions must have matching dimensions")
    return {
        "texture": texture_report(original, restored),
        "original_box": list(original_box),
        "restored_box": list(restored_box),
        "alignment_verified": False,
        "identity_verified": False,
        "release_allowed": False,
        "human_review_required": True,
    }
