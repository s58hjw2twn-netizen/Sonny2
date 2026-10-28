"""Research-only JPEG/PNG comparison with bounded proposed translation."""
from sonny_vision.quality.photo_adapter import load_grayscale
from sonny_vision.quality.face_regions import crop_region
from sonny_vision.quality.translation_search import estimate_translation
from sonny_vision.quality.texture import texture_report


def compare_auto_aligned_regions(original_path, restored_path, box, *, max_shift=3):
    original = load_grayscale(original_path)
    restored = load_grayscale(restored_path)
    proposed = estimate_translation(original, restored, box, max_shift=max_shift)
    result = {
        "registration": proposed,
        "texture": None,
        "identity_verified": False,
        "alignment_verified": False,
        "release_allowed": False,
        "human_review_required": True,
    }
    if not proposed["accepted"]:
        return result
    left, top, right, bottom = box
    dx, dy = proposed["dx"], proposed["dy"]
    a = crop_region(original, box)
    b = crop_region(restored, (left + dx, top + dy, right + dx, bottom + dy))
    result["texture"] = texture_report(a, b)
    return result
