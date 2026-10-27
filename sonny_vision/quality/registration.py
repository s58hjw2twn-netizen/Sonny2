"""Explicit integer-translation registration for already annotated face crops.

No automatic face recognition or identity inference. Translation is supplied
by a human or independent registration tool and is never estimated here.
"""
from sonny_vision.quality.photo_adapter import load_grayscale
from sonny_vision.quality.face_regions import crop_region
from sonny_vision.quality.texture import texture_report


def translated_box(box, dx, dy):
    if type(dx) is not int or type(dy) is not int:
        raise ValueError("translation must use integer pixel offsets")
    if not isinstance(box, (list, tuple)) or len(box) != 4 or any(type(v) is not int for v in box):
        raise ValueError("invalid original face box")
    return tuple(v + (dx if i % 2 == 0 else dy) for i, v in enumerate(box))


def compare_translated_region(original_path, restored_path, original_box, *, dx=0, dy=0):
    """Compare equally sized regions after explicit, externally determined shift."""
    original_grid = load_grayscale(original_path)
    restored_grid = load_grayscale(restored_path)
    restored_box = translated_box(original_box, dx, dy)
    original = crop_region(original_grid, original_box)
    restored = crop_region(restored_grid, restored_box)
    return {
        "texture": texture_report(original, restored),
        "original_box": list(original_box),
        "restored_box": list(restored_box),
        "translation": {"dx": dx, "dy": dy},
        "alignment_verified": False,
        "identity_verified": False,
        "release_allowed": False,
        "human_review_required": True,
    }
