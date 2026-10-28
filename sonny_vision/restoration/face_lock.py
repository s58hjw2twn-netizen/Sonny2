"""Face Lock v1: preserve original RGB pixels inside protected rectangles.

The source and enhanced arrays must have identical geometry. This module
does not detect faces, reconstruct details, or approve customer delivery.
"""
from math import ceil, floor
from sonny_vision.restoration.face_protection import protected_boxes


def face_lock_composite(original, enhanced, face_boxes, *, expected_faces):
    if type(expected_faces) is not int or expected_faces < 1:
        raise ValueError("explicit positive face count required")
    boxes = list(face_boxes)
    if len(boxes) != expected_faces:
        raise ValueError("face count mismatch; fail closed")
    protected = protected_boxes(boxes, padding=0.20)
    if not isinstance(original, (list, tuple)) or not original:
        raise ValueError("empty original image")
    height = len(original)
    width = len(original[0])
    if width < 2 or height < 2 or len(enhanced) != height:
        raise ValueError("invalid image dimensions")
    for grid in (original, enhanced):
        if any(len(row) != width for row in grid):
            raise ValueError("image dimensions mismatch")
        for row in grid:
            for pixel in row:
                if not isinstance(pixel, (list, tuple)) or len(pixel) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in pixel):
                    raise ValueError("invalid RGB pixel")
    locked = set()
    for left, top, right, bottom in protected:
        for y in range(max(0, floor(top * height)), min(height, ceil(bottom * height))):
            for x in range(max(0, floor(left * width)), min(width, ceil(right * width))):
                locked.add((x, y))
    result = [[tuple(original[y][x]) if (x,y) in locked else tuple(enhanced[y][x])
               for x in range(width)] for y in range(height)]
    if not locked:
        raise ValueError("empty face protection mask")
    return {"pixels": result, "protected_pixel_count": len(locked),
            "protected_pixels_identical": all(result[y][x] == tuple(original[y][x]) for x,y in locked),
            "identity_verified": False, "release_allowed": False,
            "human_review_required": True}
