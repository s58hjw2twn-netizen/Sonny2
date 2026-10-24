import unittest
from dataclasses import replace

from sonny_one.causal_evidence import make_receipt
from sonny_one.causal_self_model import CausalSelfModel
from sonny_one.causal_signed_review import (
    sign_review, verify_signed_review, record_signed_review,
)


class SignedReviewTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * 32
        self.keys = {"reviewer": self.key}
        self.nonces = set()
        self.model = CausalSelfModel({"test": True})
        self.model.predict("t1", "test", 0.6, "test fixture")
        self.receipt = make_receipt("t1", "test-runner", b"passed")
        self.review = sign_review("t1", self.receipt.digest, True, "reviewer",
                                  "unique-nonce-1", key=self.key)

    def test_valid_signature(self):
        self.assertTrue(verify_signed_review(self.review, reviewer_keys=self.keys,
                                             consumed_nonces=self.nonces))

    def test_tampered_verdict_rejected(self):
        self.assertFalse(verify_signed_review(replace(self.review, succeeded=False),
                                              reviewer_keys=self.keys,
                                              consumed_nonces=self.nonces))

    def test_unknown_reviewer_rejected(self):
        self.assertFalse(verify_signed_review(self.review, reviewer_keys={},
                                              consumed_nonces=self.nonces))

    def test_signed_observation(self):
        record_signed_review(self.model, self.receipt, b"passed", self.review,
                             reviewer_keys=self.keys, consumed_nonces=self.nonces)
        self.assertEqual(self.model.report()["observed"], 1)
        self.assertIn(("reviewer", "unique-nonce-1"), self.nonces)

    def test_replay_rejected(self):
        record_signed_review(self.model, self.receipt, b"passed", self.review,
                             reviewer_keys=self.keys, consumed_nonces=self.nonces)
        self.assertFalse(verify_signed_review(self.review, reviewer_keys=self.keys,
                                              consumed_nonces=self.nonces))

    def test_wrong_payload_rejected_without_consuming_nonce(self):
        with self.assertRaises(ValueError):
            record_signed_review(self.model, self.receipt, b"failed", self.review,
                                 reviewer_keys=self.keys, consumed_nonces=self.nonces)
        self.assertEqual(self.nonces, set())

    def test_short_key_rejected(self):
        with self.assertRaises(ValueError):
            sign_review("t1", self.receipt.digest, True, "reviewer", "n",
                        key=b"short")


if __name__ == "__main__":
    unittest.main()
