"""Face Lock for PNG/JPEG source files, producing a lossless PNG review artifact.

Uses Pillow only when invoked. No generative edits, face detection, or delivery.
"""
from hashlib import sha256
from math import floor, ceil
from pathlib import Path
from sonny_vision.restoration.face_protection import protected_boxes


def compose_face_locked_png(original_path, enhanced_path, output_path, boxes, *, expected_faces, max_pixels=4000000):
    if type(expected_faces) is not int or expected_faces < 1:
        raise ValueError("positive expected face count required")
    faces = list(boxes)
    if len(faces) != expected_faces:
        raise ValueError("face count mismatch")
    regions = protected_boxes(faces, padding=.20)
    if type(max_pixels) is not int or max_pixels < 4:
        raise ValueError("invalid pixel limit")
    destination = Path(output_path)
    if destination.suffix.lower() != ".png":
        raise ValueError("lossless PNG output required")
    if destination.resolve() in (Path(original_path).resolve(), Path(enhanced_path).resolve()):
        raise ValueError("cannot overwrite input")
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("optional Pillow dependency required") from exc
    with Image.open(original_path) as original_file, Image.open(enhanced_path) as enhanced_file:
        if original_file.format not in ("JPEG","PNG") or enhanced_file.format not in ("JPEG","PNG"):
            raise ValueError("only JPEG and PNG sources supported")
        if original_file.size != enhanced_file.size:
            raise ValueError("source dimensions differ; registration required")
        width, height = original_file.size
        if width < 2 or height < 2 or width * height > max_pixels:
            raise ValueError("invalid or oversized image")
        original = original_file.convert("RGB")
        composite = enhanced_file.convert("RGB")
        mask = Image.new("1", (width, height), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        for l,t,r,b in regions:
            left,top = max(0,floor(l*width)),max(0,floor(t*height))
            right,bottom = min(width,ceil(r*width)),min(height,ceil(b*height))
            if left >= right or top >= bottom:
                raise ValueError("empty protected region")
            draw.rectangle((left,top,right-1,bottom-1),fill=1)
        composite.paste(original,(0,0),mask)
        original_bytes=original.tobytes()
        composite_bytes=composite.tobytes()
        mask_bytes=mask.tobytes()
        # Exact check on protected pixels; no perceptual or identity claim.
        for y in range(height):
            for x in range(width):
                if mask.getpixel((x,y)):
                    if composite.getpixel((x,y)) != original.getpixel((x,y)):
                        raise AssertionError("protected pixel changed")
        composite.save(destination,format="PNG")
        return {"original_rgb_sha256":sha256(original_bytes).hexdigest(),
                "composite_rgb_sha256":sha256(composite_bytes).hexdigest(),
                "mask_sha256":sha256(mask_bytes).hexdigest(),
                "protected_pixels_identical":True,
                "identity_verified":False,"release_allowed":False,
                "human_review_required":True,"output_path":str(destination)}
