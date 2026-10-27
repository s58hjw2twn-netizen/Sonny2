import json
import tempfile
import unittest
from pathlib import Path
from sonny_vision.quality.evidence_harness import evaluate_bundle, evaluate_file

FACE={"left_eye":[.3,.3],"right_eye":[.7,.3],"nose":[.5,.5],
      "mouth_left":[.4,.7],"mouth_right":[.6,.7],"chin":[.5,.9]}
CROP=[[.2,.6,.2],[.6,.2,.6],[.2,.6,.2]]
def bundle():
    return {"faces":[{"landmark_stages":[FACE,FACE],"original_crop":CROP,
                      "restored_crop":CROP}],"identity_scores":[.99],
            "reference_review_passed":True,"owner_approved":True}

class EvidenceHarnessTests(unittest.TestCase):
    def test_complete_bundle_is_provisional(self):
        result=evaluate_bundle(bundle())
        self.assertTrue(result["release_allowed"])
        self.assertFalse(result["automated_delivery_allowed"])
        self.assertFalse(result["identity_verified"])
    def test_missing_approval_blocks(self):
        data=bundle()
        data.pop("owner_approved")
        self.assertFalse(evaluate_bundle(data)["release_allowed"])
    def test_invalid_bundle_blocks(self):
        with self.assertRaises(ValueError):
            evaluate_bundle({})
    def test_file_fingerprint_stable(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"evidence.json"
            path.write_text(json.dumps(bundle()),encoding="utf-8")
            a=evaluate_file(path)
            b=evaluate_file(path)
            self.assertEqual(a["evidence_sha256"],b["evidence_sha256"])
            self.assertEqual(len(a["evidence_sha256"]),64)
