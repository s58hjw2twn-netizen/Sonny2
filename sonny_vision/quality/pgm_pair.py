"""Evaluate a registered grayscale image pair without modifying either file."""
import hashlib
from pathlib import Path

from sonny_vision.quality.pgm_fixture import read_pgm
from sonny_vision.quality.texture import texture_report


def evaluate_pgm_pair(original_path, restored_path):
    original_bytes = Path(original_path).read_bytes()
    restored_bytes = Path(restored_path).read_bytes()
    original = read_pgm(original_path)
    restored = read_pgm(restored_path)
    result = texture_report(original, restored)
    return {
        "texture": result,
        "original_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "restored_sha256": hashlib.sha256(restored_bytes).hexdigest(),
        "identity_verified": False,
        "release_allowed": False,
        "human_review_required": True,
        "registration_verified": False,
    }
