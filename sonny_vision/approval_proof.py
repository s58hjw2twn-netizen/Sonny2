"""Generate customer approval proofs without exposing the restored master.

Proofs are visibly watermarked, resized, and separately encoded. The clean
master remains untouched and must not be exposed by a preview endpoint.
"""
from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np

PROOF_LABEL = "SONNY VISION - PROOF - NOT FOR DELIVERY"


def make_approval_proof(image: np.ndarray, max_edge: int = 1200) -> bytes:
    if image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected uint8 BGR image")
    height, width = image.shape[:2]
    if min(height, width) < 16 or not 320 <= max_edge <= 1600:
        raise ValueError("Invalid image or proof dimensions")
    scale = min(1.0, max_edge / max(height, width))
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    proof = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA).copy()
    h, w = proof.shape[:2]
    overlay = proof.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    size = max(0.38, min(w, h) / 950)
    thickness = max(1, round(size * 2))
    step_y = max(100, round(h / 4))
    for row, y in enumerate(range(step_y // 2, h, step_y)):
        label = PROOF_LABEL
        (tw, th), _ = cv2.getTextSize(label, font, size, thickness)
        # Repeat across the image, including its central area.
        for x in range(-tw // 3 + (row % 2) * (tw // 2), w, max(1, tw + 45)):
            cv2.putText(overlay, label, (x, min(h - 8, y)), font, size,
                        (255, 255, 255), thickness + 2, cv2.LINE_AA)
            cv2.putText(overlay, label, (x, min(h - 8, y)), font, size,
                        (25, 25, 25), thickness, cv2.LINE_AA)
    proof = cv2.addWeighted(overlay, 0.48, proof, 0.52, 0)
    # Persistent center label makes cropping a corner watermark insufficient.
    center = "APPROVAL PREVIEW"
    center_size = max(0.55, min(w, h) / 720)
    (tw, _), _ = cv2.getTextSize(center, font, center_size, 2)
    cv2.putText(proof, center, (max(0, (w - tw) // 2), h // 2),
                font, center_size, (245, 245, 245), 3, cv2.LINE_AA)
    ok, encoded = cv2.imencode(".jpg", proof, [cv2.IMWRITE_JPEG_QUALITY, 78])
    if not ok:
        raise RuntimeError("Proof encoding failed")
    return encoded.tobytes()


def write_approval_proof(master_path: str, proof_path: str, max_edge: int = 1200) -> None:
    master, destination = Path(master_path), Path(proof_path)
    if master.resolve() == destination.resolve():
        raise ValueError("Cannot overwrite the master")
    if destination.suffix.lower() not in {".jpg", ".jpeg"}:
        raise ValueError("Proof must use JPEG extension")
    image = cv2.imread(str(master), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to read master image")
    proof_bytes = make_approval_proof(image, max_edge)
    with destination.open("xb") as out:
        out.write(proof_bytes)
