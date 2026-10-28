"""External evaluator protocol validates request shape but authorizes no execution."""
import unittest
from sonny_one.apl.evaluator_protocol import validate_external_evaluator_request

VALID = {"candidate_sha256": "a" * 64, "base_revision": "b" * 40,
         "suite_sha256": "c" * 64}


class EvaluatorProtocolTests(unittest.TestCase):
    def test_valid_request_has_no_execution_or_signing_authority(self):
        result = validate_external_evaluator_request(VALID)
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["signature_authorized"])
        self.assertFalse(result["confidentiality_verified"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_malformed_requests_rejected(self):
        cases = [{**VALID, "candidate_sha256": "bad"},
                 {**VALID, "base_revision": "main"},
                 {**VALID, "suite_sha256": "bad"},
                 {**VALID, "extra": "attacker-controlled"},
                 None, []]
        for request in cases:
            with self.subTest(request=request), self.assertRaises(ValueError):
                validate_external_evaluator_request(request)


if __name__ == "__main__":
    unittest.main()
