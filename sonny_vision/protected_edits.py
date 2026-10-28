"""Fail-closed validation for localized Sonny Vision edits.

This module validates a proposed output; it does not generate or approve edits.
Requires Pillow. All coordinates are half-open (left, top, right, bottom).
"""
from PIL import Image, ImageChops


class ProtectedEditError(ValueError):
    pass


def validate_local_edit(original_path, candidate_path, allowed_regions):
    """Reject any changed pixel outside explicitly authorized rectangles.

    Returns a small audit summary. Both images must have identical dimensions,
    and comparison uses RGBA to avoid hidden palette/color-mode differences.
    A passing pixel check does NOT verify insignia orientation or face identity.
    """
    with Image.open(original_path) as source, Image.open(candidate_path) as proposed:
        if source.size != proposed.size:
            raise ProtectedEditError("Image dimensions changed")
        width, height = source.size
        if not allowed_regions:
            raise ProtectedEditError("No authorized edit regions")
        for region in allowed_regions:
            if len(region) != 4 or any(type(v) is not int for v in region):
                raise ProtectedEditError("Invalid region coordinates")
            left, top, right, bottom = region
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise ProtectedEditError("Region outside image")
        before = source.convert("RGBA")
        after = proposed.convert("RGBA")
        diff = ImageChops.difference(before, after)
        bounds = tuple(channel.getbbox() for channel in diff.split())
        if all(bound is None for bound in bounds):
            return {"changed_pixels": 0, "status": "no_change"}
        changed = 0
        pixels = diff.load()
        for y in range(height):
            for x in range(width):
                if pixels[x, y] != (0, 0, 0, 0):
                    changed += 1
                    if not any(l <= x < r and t <= y < b for l, t, r, b in allowed_regions):
                        raise ProtectedEditError(
                            "Unauthorized pixel change outside edit regions"
                        )
        return {"changed_pixels": changed, "status": "pixel_boundary_pass"}
