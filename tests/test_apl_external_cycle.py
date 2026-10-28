"""External evaluation envelope integrity and no-promotion behavior."""
import unittest
from unittest.mock import patch

from sonny_one.apl.external_cycle import (
    prepare_external_evaluation, review_external_evaluation,
)


class ExternalCycleTests(unittest.TestCase):
    def setUp(self):
        self.prepared = prepare_external_evaluation(
            b"candidate-patch", base_revision="b" * 40,
            suite_sha256="c" * 64)
        self.kwargs = dict(trusted_evaluator_id="lab",
                           trusted_public_key_pem=b"pinned-key",
                           trusted_public_key_sha256="d" * 64)

    @patch("sonny_one.apl.external_cycle.review_pinned_holdout_request")
    def test_prepared_manifest_binds_review(self, verifier):
        verifier.return_value = {"signature_verified": True}
        result = review_external_evaluation(
            self.prepared, {"signature": "external"}, **self.kwargs)
        self.assertEqual(result["request_sha256"], self.prepared["request_sha256"])
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(verifier.call_args.args[0], self.prepared["request"])

    @patch("sonny_one.apl.external_cycle.review_pinned_holdout_request")
    def test_tampered_request_rejected_before_review(self, verifier):
        tampered = dict(self.prepared)
        tampered["request"] = {**tampered["request"], "suite_sha256": "d" * 64}
        with self.assertRaises(ValueError):
            review_external_evaluation(tampered, {}, **self.kwargs)
        verifier.assert_not_called()

    @patch("sonny_one.apl.external_cycle.review_pinned_holdout_request")
    def test_extra_envelope_field_rejected(self, verifier):
        with self.assertRaises(ValueError):
            review_external_evaluation({**self.prepared, "promotion": "ALLOWED"},
                                       {}, **self.kwargs)
        verifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
