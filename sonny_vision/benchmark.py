"""Compare archival candidates without claiming perceptual or identity validation.

Usage: python -m sonny_vision.benchmark original.jpg v16.png v17.png
No images are uploaded, modified or exported.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from .archival_engine import analyze, restore_archival


def load(path: str) -> np.ndarray:
    raw = np.frombuffer(Path(path).read_bytes(), dtype=np.uint8)
    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Unable to decode image: " + path)
    return img


def compare(source: np.ndarray, candidate: np.ndarray) -> dict:
    if source.shape != candidate.shape:
        raise ValueError("Comparison requires identical image dimensions")
    delta = np.abs(source.astype(np.float32) - candidate.astype(np.float32))
    metrics = analyze(candidate)
    return {
        "mean_absolute_channel_change": round(float(delta.mean()), 4),
        "p99_channel_change": round(float(np.percentile(delta, 99)), 4),
        "contrast_std": round(metrics.contrast_std, 4),
        "clipping_fraction": round(metrics.clipping_fraction, 6),
        "blur_variance": round(metrics.blur_variance, 4),
        "identity_verified": False,
        "perceptual_improvement_verified": False,
        "release_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("original")
    parser.add_argument("v16")
    parser.add_argument("v17", nargs="?")
    args = parser.parse_args()
    original = load(args.original)
    v16 = load(args.v16)
    v17 = load(args.v17) if args.v17 else restore_archival(original)
    print(json.dumps({
        "v16_vs_original": compare(original, v16),
        "v17_vs_original": compare(original, v17),
        "v17_vs_v16": compare(v16, v17),
        "note": "Numerical diagnostics are not evidence of visual superiority or identity preservation.",
    }, indent=2))


if __name__ == "__main__":
    main()
