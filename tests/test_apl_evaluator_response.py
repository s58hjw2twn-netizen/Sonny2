"""External evaluator response binding is necessary but never sufficient."""
import unittest
from sonny_one.apl.evaluator_response import validate_evaluator_response

REQUEST = {"candidate_sha256": "a" * 64, "base_revision": "b" * 40,
           "suite_sha256": "c" * 64}


def response():
    return {**REQUEST, "evaluator_id": "separate-lab", "result": "PASS",
            "signature": "unverified", "schema_version": 1}


class EvaluatorResponseTests(unittest.TestCase):
    def test_matching_response_remains_untrusted(self):
        result = validate_evaluator_response(REQUEST, response())
        self.assertTrue(result["response_matches_request"])
        self.assertFalse(result["signature_verified"])
        self.assertFalse(result["confidentiality_verified"])
        self.assertFalse(result["independent_custody_verified"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_mismatched_or_malformed_response_rejected(self):
        for field, value in (("candidate_sha256", "d" * 64),
                             ("base_revision", "e" * 40),
                             ("suite_sha256", "f" * 64),
                             ("evaluator_id", ""),
                             ("result", "PROMOTE"),
                             ("signature", ""),
                             ("schema_version", 2)):
            item = response()
            item[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_evaluator_response(REQUEST, item)

    def test_extra_fields_rejected(self):
        with self.assertRaises(ValueError):
            validate_evaluator_response(REQUEST, {**response(), "trusted": True})


if __name__ == "__main__":
    unittest.main()
