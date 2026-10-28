"""External evidence review must not grant autonomous promotion."""
import unittest
from unittest.mock import patch
from sonny_one.apl.external_review import review_external_holdout


class ExternalReviewTests(unittest.TestCase):
    @patch("sonny_one.apl.external_review.verify_with_pinned_evaluator")
    def test_signed_pass_stays_review_only(self, verifier):
        verifier.return_value = {
            "attestation_sha256": "c" * 64,
            "signature_verified": True,
            "evaluator_key_pin_verified": True,
            "result_untrusted": "PASS",
        }
        result = review_external_holdout(
            {"result": "PASS"}, candidate_sha256="a" * 64,
            base_revision="b" * 40, trusted_evaluator_id="lab",
            trusted_public_key_pem=b"pinned", trusted_public_key_sha256="d" * 64)
        self.assertTrue(result["signature_verified"])
        self.assertFalse(result["independent_custody_verified"])
        self.assertFalse(result["confidential_execution_verified"])
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")
        verifier.assert_called_once()


if __name__ == "__main__":
    unittest.main()
