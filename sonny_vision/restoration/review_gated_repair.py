"""Review-gated scratch repair. Research-only; no automatic approval.

Review records require a trusted-backend HMAC signature. Possession of a signing
key does not itself authenticate a human reviewer; backend auth is still required.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from sonny_vision.restoration.review_authorization import verify_review


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, proposal_file, decisions_file, output, *, protected_rectangles, authorization_secret, expected_reviewer_id=None):
    source, proposal_file, decisions_file, output = map(Path, (source, proposal_file, decisions_file, output))
    if output.suffix.lower() != ".png" or output.resolve() in (
        source.resolve(), proposal_file.resolve(), decisions_file.resolve()):
        raise ValueError("output must be a separate PNG")
    proposal = json.loads(proposal_file.read_text())
    decisions = json.loads(decisions_file.read_text())
    if proposal.get("source_sha256") != digest(source) or decisions.get("source_sha256") != digest(source):
        raise ValueError("source digest mismatch")
    if decisions.get("proposal_sha256") != digest(proposal_file):
        raise ValueError("proposal digest mismatch")
    verify_review(decisions, authorization_secret, expected_reviewer_id=expected_reviewer_id)
    if decisions.get("reviewer_confirmed") is not True:
        raise ValueError("explicit review confirmation required")
    candidates = proposal.get("proposals")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("nonempty proposal list required")
    ids = [c.get("id") for c in candidates]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("duplicate or invalid candidate IDs")
    votes = decisions.get("decisions")
    if not isinstance(votes, list) or len(votes) != len(ids):
        raise ValueError("explicit decision for each candidate required")
    voted_ids = [v.get("id") for v in votes]
    if len(set(voted_ids)) != len(voted_ids) or set(voted_ids) != set(ids):
        raise ValueError("missing, duplicate, or unknown decision ID")
    if any(v.get("decision") not in ("approve", "reject") for v in votes):
        raise ValueError("invalid decision")
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow, numpy and OpenCV are required for repair execution") from exc
    with Image.open(source) as im:
        if im.format not in ("PNG", "JPEG"):
            raise ValueError("only PNG and JPEG input supported")
        image = np.asarray(im.convert("RGB")).copy()
    h, w = image.shape[:2]
    blocked = np.zeros((h, w), dtype=bool)
    regions = list(protected_rectangles)
    if not regions:
        raise ValueError("protected person regions required")
    for box in regions:
        if len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError("invalid protected rectangle")
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h):
            raise ValueError("invalid protected rectangle")
        blocked[y1:y2, x1:x2] = True
    mask = np.zeros((h, w), dtype=np.uint8)
    by_id = dict(zip(ids, candidates))
    approved = []
    for vote in votes:
        if vote["decision"] == "reject":
            continue
        box = by_id[vote["id"]].get("bbox_xyxy")
        if not isinstance(box, list) or len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError("invalid candidate rectangle")
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h):
            raise ValueError("invalid candidate rectangle")
        if blocked[y1:y2, x1:x2].any():
            raise ValueError("approved repair intersects protected region")
        mask[y1:y2, x1:x2] = 255
        approved.append(vote["id"])
    if approved:
        repaired_bgr = cv2.inpaint(cv2.cvtColor(image, cv2.COLOR_RGB2BGR), mask, 3, cv2.INPAINT_TELEA)
        result = cv2.cvtColor(repaired_bgr, cv2.COLOR_BGR2RGB)
    else:
        result = image.copy()
    changed = np.any(result != image, axis=2)
    if np.any(changed & (mask == 0)) or np.any(changed & blocked):
        raise AssertionError("unauthorized pixel change")
    Image.fromarray(result).save(output, format="PNG")
    return {"approved_candidate_ids": approved,
            "changed_pixels": int(changed.sum()),
            "changed_outside_approved_mask": int(np.count_nonzero(changed & (mask == 0))),
            "changed_inside_protected_regions": int(np.count_nonzero(changed & blocked)),
            "source_sha256": digest(source), "output_sha256": digest(output),
            "reviewer_identity_verified": False, "identity_verified": False,
            "release_allowed": False, "human_review_required": True}
