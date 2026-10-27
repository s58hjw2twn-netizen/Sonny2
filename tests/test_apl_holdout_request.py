"""Trusted request must match signed external evidence before review."""
import unittest
from unittest.mock import patch
from sonny_one.apl.holdout_request import review_pinned_holdout_request

REQUEST = dict(candidate_sha256="a" * 64, base_revision="b" * 40,
               suite_sha256="c" * 64)


class HoldoutRequestTests(unittest.TestCase):
    def review(self, request=None, attestation=None):
        return review_pinned_holdout_request(
            REQUEST if request is None else request,
            {"suite_sha256": "c" * 64} if attestation is None else attestation,
            trusted_evaluator_id="lab", trusted_public_key_pem=b"trusted",
            trusted_public_key_sha256="d" * 64)

    @patch("sonny_one.apl.holdout_request.review_external_holdout")
    def test_matched_request_is_review_only(self, verifier):
        verifier.return_value = {"signature_verified": True}
        result = self.review()
        self.assertTrue(result["trusted_request_binding_verified"])
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertEqual(verifier.call_args.kwargs["candidate_sha256"], "a" * 64)

    @patch("sonny_one.apl.holdout_request.review_external_holdout")
    def test_suite_mismatch_rejected_before_signature_review(self, verifier):
        with self.assertRaises(ValueError):
            self.review(attestation={"suite_sha256": "d" * 64})
        verifier.assert_not_called()

    @patch("sonny_one.apl.holdout_request.review_external_holdout")
    def test_invalid_trusted_request_rejected(self, verifier):
        for request in (
            {**REQUEST, "candidate_sha256": "wrong"},
            {**REQUEST, "base_revision": "wrong"},
            {**REQUEST, "suite_sha256": "wrong"},
            {**REQUEST, "extra": True},
        ):
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.review(request=request)
        verifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
