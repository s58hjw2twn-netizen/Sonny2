import hashlib
import unittest
from dataclasses import replace
from sonny_vision.review_gate_v17 import (
    sign_decision, verify_decision, authorize_customer_release,
)

class ReviewGateV17Tests(unittest.TestCase):
    def setUp(self):
        self.secret = b"x" * 32
        self.source = b"source-image-bytes"
        self.output = b"restored-image-bytes"
        self.s = hashlib.sha256(self.source).hexdigest()
        self.o = hashlib.sha256(self.output).hexdigest()

    def test_missing_review_denied(self):
        self.assertFalse(authorize_customer_release(None, self.source, self.output,
                                                     self.secret, True, True))

    def test_candidate_approval_not_release(self):
        d = sign_decision(self.s, self.o, "operator", "candidate_review", True, self.secret)
        self.assertFalse(authorize_customer_release(d, self.source, self.output,
                                                     self.secret, True, True))

    def test_changed_output_denied(self):
        d = sign_decision(self.s, self.o, "operator", "customer_release", True, self.secret)
        self.assertFalse(authorize_customer_release(d, self.source, b"tampered",
                                                     self.secret, True, True))

    def test_changed_signature_denied(self):
        d = sign_decision(self.s, self.o, "operator", "customer_release", True, self.secret)
        self.assertFalse(verify_decision(replace(d, signature="0" * 64),
                                         self.s, self.o, "customer_release", self.secret))

    def test_quality_or_identity_failure_denied(self):
        d = sign_decision(self.s, self.o, "operator", "customer_release", True, self.secret)
        for quality, identity in [(False, True), (True, False)]:
            self.assertFalse(authorize_customer_release(d, self.source, self.output,
                                                         self.secret, quality, identity))

    def test_valid_explicit_release(self):
        d = sign_decision(self.s, self.o, "operator", "customer_release", True, self.secret)
        self.assertTrue(authorize_customer_release(d, self.source, self.output,
                                                    self.secret, True, True))

if __name__ == "__main__":
    unittest.main()
