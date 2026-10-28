import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from sonny_vision.restoration.review_draft_bridge import validate_review_draft

class DraftBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.source=root/"photo.png"; self.source.write_bytes(b"private-test-photo")
        self.proposal=root/"proposal.json"; self.draft=root/"draft.json"
        self.manifest={"source_sha256":hashlib.sha256(self.source.read_bytes()).hexdigest(),
                       "proposals":[{"id":"P1","bbox_xyxy":[0,0,1,1]}]}
        self.proposal.write_text(json.dumps(self.manifest))
        self.record={"source_sha256":self.manifest["source_sha256"],
          "proposal_sha256":hashlib.sha256(self.proposal.read_bytes()).hexdigest(),
          "authorization_status":"UNSIGNED_REVIEW_DRAFT","reviewer_confirmed":False,
          "decisions":[{"id":"P1","decision":"reject"}]}
        self.save()
    def save(self): self.draft.write_text(json.dumps(self.record))
    def check(self): return validate_review_draft(self.source,self.proposal,self.draft)
    def test_valid_draft_not_authorized(self):
        result=self.check()
        self.assertEqual(result["reject_count"],1)
        self.assertFalse(result["repair_permitted"])
    def test_missing_vote(self):
        self.record["decisions"]=[]; self.save()
        with self.assertRaises(ValueError): self.check()
    def test_tampered_source(self):
        self.source.write_bytes(b"changed")
        with self.assertRaises(ValueError): self.check()
    def test_tampered_proposal(self):
        self.manifest["proposals"].append({"id":"P2","bbox_xyxy":[1,1,2,2]})
        self.proposal.write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError): self.check()
    def test_forged_confirmation(self):
        self.record["reviewer_confirmed"]=True; self.save()
        with self.assertRaises(ValueError): self.check()
    def test_fake_signature(self):
        self.record["authorization_hmac_sha256"]="a"*64; self.save()
        with self.assertRaises(ValueError): self.check()
    def test_unknown_vote(self):
        self.record["decisions"][0]["id"]="UNKNOWN"; self.save()
        with self.assertRaises(ValueError): self.check()
