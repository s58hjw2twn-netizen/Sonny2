"""Optional Pillow adapter for JPEG/PNG face-crop texture evaluation.

Pillow must be installed separately after dependency/license review.
No face detection, alignment, identity verification or reconstruction occurs.
"""
from pathlib import Path
from sonny_vision.quality.texture import texture_report

MAX_PIXELS = 4_000_000

def load_grayscale(path, *, max_pixels=MAX_PIXELS):
    if not isinstance(max_pixels, int) or isinstance(max_pixels, bool) or max_pixels < 4:
        raise ValueError("invalid pixel limit")
    suffix = Path(path).suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg"):
        raise ValueError("only PNG and JPEG supported")
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise RuntimeError("Pillow is required for PNG/JPEG; install only after dependency review") from exc
    try:
        with Image.open(path) as image:
            if image.format not in ("PNG", "JPEG"):
                raise ValueError("image content does not match accepted formats")
            width, height = image.size
            if width < 2 or height < 2 or width * height > max_pixels:
                raise ValueError("invalid or oversized image")
            gray = image.convert("L")
            values = list(gray.getdata())
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("unreadable image") from exc
    return [[values[y * width + x] / 255.0 for x in range(width)]
            for y in range(height)]

def compare_image_pair(original_path, restored_path, *, max_pixels=MAX_PIXELS):
    original = load_grayscale(original_path, max_pixels=max_pixels)
    restored = load_grayscale(restored_path, max_pixels=max_pixels)
    return {
        "texture": texture_report(original, restored),
        "identity_verified": False,
        "registration_verified": False,
        "release_allowed": False,
        "human_review_required": True,
    }
