import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from sonny_vision.restoration.review_gated_repair import run, digest
from sonny_vision.restoration.review_authorization import sign_review

class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        try:
            import cv2
            import numpy
            from PIL import Image
        except ImportError:
            self.skipTest("optional repair dependencies unavailable")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = Path(self.tmp.name)
        self.src, self.proposal, self.votes, self.out = (p / n for n in ("src.png", "proposal.json", "votes.json", "out.png"))
        im = Image.new("RGB", (24,24), (180,180,180))
        im.putpixel((18,18), (0,0,0))
        im.save(self.src)
        self.manifest = {"source_sha256":digest(self.src), "proposals":[{"id":"A","bbox_xyxy":[16,16,21,21]}]}
        self.write()
    def write(self):
        self.proposal.write_text(json.dumps(self.manifest))
        self.decisions = getattr(self, "decisions", {"source_sha256":digest(self.src), "reviewer_confirmed":True, "decisions":[{"id":"A","decision":"approve"}]})
        self.decisions["proposal_sha256"] = digest(self.proposal)
        self.decisions["reviewer_id"] = "trusted-reviewer"
        self.decisions["authorization_hmac_sha256"] = sign_review(self.decisions, b"k"*32)
        self.votes.write_text(json.dumps(self.decisions))
    def run_gate(self):
        return run(self.src,self.proposal,self.votes,self.out,protected_rectangles=[(0,0,10,10)],authorization_secret=b"k"*32,expected_reviewer_id="trusted-reviewer")
    def test_approved_changes_are_bounded(self):
        r=self.run_gate()
        self.assertGreater(r["changed_pixels"],0)
        self.assertEqual(r["changed_outside_approved_mask"],0)
        self.assertEqual(r["changed_inside_protected_regions"],0)
        self.assertFalse(r["release_allowed"])
    def test_reject_all_keeps_pixels(self):
        self.decisions["decisions"][0]["decision"]="reject"
        self.write()
        r=self.run_gate()
        self.assertEqual(r["changed_pixels"],0)
    def test_missing_review_rejected(self):
        self.decisions["reviewer_confirmed"]=False
        self.write()
        with self.assertRaises(ValueError): self.run_gate()
    def test_missing_decision_rejected(self):
        self.decisions["decisions"]=[]
        self.write()
        with self.assertRaises(ValueError): self.run_gate()
    def test_source_digest_mismatch_rejected(self):
        self.decisions["source_sha256"]="0"*64
        self.write()
        with self.assertRaises(ValueError): self.run_gate()
    def test_face_overlap_rejected(self):
        self.manifest["proposals"][0]["bbox_xyxy"]=[3,3,8,8]
        self.write()
        with self.assertRaises(ValueError): self.run_gate()
    def test_duplicate_candidates_rejected(self):
        self.manifest["proposals"].append(dict(self.manifest["proposals"][0]))
        self.write()
        with self.assertRaises(ValueError): self.run_gate()

    def test_tampered_signed_approval_rejected(self):
        self.decisions["decisions"][0]["decision"]="reject"
        self.votes.write_text(json.dumps(self.decisions))
        with self.assertRaises(ValueError): self.run_gate()
    def test_missing_authorization_secret_rejected(self):
        with self.assertRaises(TypeError):
            run(self.src,self.proposal,self.votes,self.out,protected_rectangles=[(0,0,10,10)])
    def test_wrong_signing_key_rejected(self):
        with self.assertRaises(ValueError):
            run(self.src,self.proposal,self.votes,self.out,protected_rectangles=[(0,0,10,10)],authorization_secret=b"x"*32)
