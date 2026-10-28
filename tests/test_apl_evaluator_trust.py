"""Pinned evaluator identity and public key validation without external deps."""
import hashlib
import unittest
from unittest.mock import patch

from sonny_one.apl.evaluator_trust import verify_with_pinned_evaluator

KEY = b"trusted-public-key"
DIGEST = hashlib.sha256(KEY).hexdigest()


class EvaluatorTrustTests(unittest.TestCase):
    def verify(self, **overrides):
        kwargs = dict(attestation={"untrusted": True},
                      candidate_sha256="a" * 64, base_revision="b" * 40,
                      trusted_evaluator_id="independent-lab",
                      trusted_public_key_pem=KEY,
                      trusted_public_key_sha256=DIGEST)
        kwargs.update(overrides)
        return verify_with_pinned_evaluator(**kwargs)

    @patch("sonny_one.apl.evaluator_trust.verify_signed_external_holdout")
    def test_correct_pin_calls_signature_verifier(self, verifier):
        verifier.return_value = {"signature_verified": True}
        result = self.verify()
        self.assertTrue(result["evaluator_key_pin_verified"])
        self.assertFalse(result["independent_custody_verified"])
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertEqual(verifier.call_args.kwargs["trusted_public_key_pem"], KEY)

    @patch("sonny_one.apl.evaluator_trust.verify_signed_external_holdout")
    def test_bad_pin_never_reaches_verifier(self, verifier):
        for changes in ({"trusted_public_key_sha256": "c" * 64},
                        {"trusted_public_key_sha256": "invalid"},
                        {"trusted_evaluator_id": "lab/unsafe"},
                        {"trusted_public_key_pem": b""}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.verify(**changes)
        verifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
