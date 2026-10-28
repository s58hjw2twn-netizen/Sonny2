"""Create a visibly watermarked review preview; never substitute it for final approval."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json

def make_review_preview(source, output, audit_output, *, case_id, max_dimension=1200):
    if not case_id or not case_id.strip():
        raise ValueError("case_id required")
    source, output, audit_output = map(Path, (source, output, audit_output))
    if source.resolve() == output.resolve():
        raise ValueError("Preview must not overwrite original")
    if source.resolve() == audit_output.resolve():
        raise ValueError("Audit must not overwrite original")
    with Image.open(source) as opened:
        img = opened.convert("RGB")
    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    label = "SONNY VISION  •  REVIEW ONLY  •  NOT APPROVED"
    font = ImageFont.load_default()
    step = max(55, img.height // 7)
    for y in range(20, img.height, step):
        for x in range(-100, img.width, 270):
            draw.text((x, y), label, fill=(255, 255, 255, 170), stroke_width=1,
                      stroke_fill=(0, 0, 0, 190), font=font)
    preview = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(output, format="PNG")
    evidence = {
        "case_id": case_id,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "preview_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "status": "watermarked_review_only",
        "customer_approved": False,
        "warning": "Watermark deters casual reuse; it cannot prevent screenshots or removal."
    }
    audit_output.parent.mkdir(parents=True, exist_ok=True)
    audit_output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence
