"""Read simple binary PGM (P5) face crops into normalized grayscale arrays.

Research fixture format only. No face detection, alignment, or image generation.
"""
from pathlib import Path


def read_pgm(path, *, max_pixels=1000000):
    data = Path(path).read_bytes()
    if not data.startswith(b"P5\n"):
        raise ValueError("expected binary PGM P5")
    header, sep, pixels = data.partition(b"\n255\n")
    if not sep:
        raise ValueError("expected max value 255")
    parts = header.split()
    if len(parts) != 3 or parts[0] != b"P5":
        raise ValueError("invalid PGM header")
    try:
        width, height = int(parts[1]), int(parts[2])
    except ValueError as exc:
        raise ValueError("invalid dimensions") from exc
    if width < 2 or height < 2 or width * height > max_pixels:
        raise ValueError("invalid or excessive dimensions")
    if len(pixels) != width * height:
        raise ValueError("incorrect pixel count")
    return [[v / 255.0 for v in pixels[y * width:(y + 1) * width]]
            for y in range(height)]
