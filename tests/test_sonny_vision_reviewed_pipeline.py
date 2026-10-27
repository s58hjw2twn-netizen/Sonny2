import hashlib
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from sonny_vision.review_gate_v17 import sign_decision
from sonny_vision.reviewed_pipeline_v17 import release_with_quality_review


class ReviewedPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source, self.candidate, self.destination = (root / n for n in ("original.png", "candidate.png", "release.png"))
        image = np.full((48, 48, 3), 110, dtype=np.uint8)
        cv2.imwrite(str(self.source), image)
        cv2.imwrite(str(self.candidate), image)
        self.mask = np.ones((48, 48), dtype=np.bool_)
        self.secret = b"k" * 32

    def decision(self):
        return sign_decision(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                             hashlib.sha256(self.candidate.read_bytes()).hexdigest(),
                             "operator", "customer_release", True, self.secret)

    def identity_decision(self):
        return sign_decision(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                             hashlib.sha256(self.candidate.read_bytes()).hexdigest(),
                             "operator", "candidate_review", True, self.secret)

    def release(self, decision, mask=None, identity=False, signed_identity=True, reviewers=frozenset({"operator"})):
        return release_with_quality_review(str(self.source), str(self.candidate),
                                           str(self.destination),
                                           self.mask if mask is None else mask,
                                           decision, self.secret, identity_reviewed=identity,
                                           identity_decision=self.identity_decision() if signed_identity else None,
                                           authorized_reviewers=reviewers)

    def test_unreviewed_identity_denied(self):
        result = self.release(self.decision())
        self.assertFalse(result["exported"])
        self.assertFalse(self.destination.exists())

    def test_missing_signature_denied(self):
        result = self.release(None, identity=True)
        self.assertFalse(result["exported"])

    def test_bad_mask_denied(self):
        result = self.release(self.decision(), mask=np.zeros_like(self.mask), identity=True)
        self.assertFalse(result["exported"])

    def test_excessive_protected_change_denied(self):
        image = cv2.imread(str(self.candidate))
        image[12:28, 12:28] = 255
        cv2.imwrite(str(self.candidate), image)
        result = self.release(self.decision(), identity=True)
        self.assertFalse(result["exported"])

    def test_unsigned_identity_review_denied(self):
        result = self.release(self.decision(), identity=True, signed_identity=False)
        self.assertFalse(result["exported"])
        self.assertFalse(self.destination.exists())

    def test_missing_reviewer_policy_denied(self):
        result = self.release(self.decision(), identity=True, reviewers=None)
        self.assertFalse(result["exported"])
        self.assertFalse(self.destination.exists())

    def test_unknown_reviewer_denied(self):
        result = self.release(self.decision(), identity=True, reviewers=frozenset({"other"}))
        self.assertFalse(result["exported"])
        self.assertFalse(self.destination.exists())

    def test_reviewed_unmodified_candidate_exports(self):
        result = self.release(self.decision(), identity=True)
        self.assertTrue(result["exported"])
        self.assertEqual(self.destination.read_bytes(), self.candidate.read_bytes())


if __name__ == "__main__":
    unittest.main()
