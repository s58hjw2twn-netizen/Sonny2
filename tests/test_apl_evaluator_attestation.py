"""Unsigned attestation builder binds result to request but proves no execution."""
import unittest
from sonny_one.apl.evaluator_attestation import build_unsigned_attestation

REQUEST = {"candidate_sha256": "a" * 64, "base_revision": "b" * 40,
           "suite_sha256": "c" * 64}


class EvaluatorAttestationTests(unittest.TestCase):
    def test_builds_unsigned_review_only_record(self):
        result = build_unsigned_attestation(
            REQUEST, evaluator_id="external-lab", suite_result="PASS")
        self.assertEqual(result["candidate_sha256"], REQUEST["candidate_sha256"])
        self.assertEqual(result["base_revision"], REQUEST["base_revision"])
        self.assertEqual(result["suite_sha256"], REQUEST["suite_sha256"])
        self.assertFalse(result["signed"])
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["confidentiality_verified"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_invalid_inputs_rejected(self):
        for request, evaluator, status in (
            ({**REQUEST, "candidate_sha256": "bad"}, "lab", "PASS"),
            ({**REQUEST, "base_revision": "main"}, "lab", "PASS"),
            ({**REQUEST, "suite_sha256": "bad"}, "lab", "PASS"),
            (REQUEST, "lab/attacker", "PASS"),
            (REQUEST, "lab", "PROMOTE"),
        ):
            with self.subTest(request=request, evaluator=evaluator, status=status), self.assertRaises(ValueError):
                build_unsigned_attestation(request, evaluator_id=evaluator, suite_result=status)


if __name__ == "__main__":
    unittest.main()
