"""External holdout evidence cannot be trusted without signature verification."""
import unittest
from sonny_one.apl.external_holdout import verify_external_holdout_attestation

SHA = "a" * 64
REV = "b" * 40


def example():
    return dict(schema_version=1, candidate_sha256=SHA, base_revision=REV,
                evaluator_id="independent-lab", suite_sha256="c" * 64,
                result="PASS", signature="not-a-verified-signature")


class ExternalHoldoutTests(unittest.TestCase):
    def verify(self, record):
        return verify_external_holdout_attestation(
            record, candidate_sha256=SHA, base_revision=REV,
            expected_evaluator="independent-lab")

    def test_unverified_attestation_never_promotes(self):
        result = self.verify(example())
        self.assertEqual(result["result_untrusted"], "PASS")
        self.assertFalse(result["signature_verified"])
        self.assertFalse(result["independent_custody_verified"])
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_mismatches_rejected(self):
        for field, value in (("candidate_sha256", "d" * 64),
                             ("base_revision", "e" * 40),
                             ("evaluator_id", "unknown"),
                             ("suite_sha256", "wrong"),
                             ("signature", ""),
                             ("result", "PROMOTE"),
                             ("schema_version", 2)):
            record = example()
            record[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.verify(record)

    def test_extra_fields_rejected(self):
        record = example()
        record["promotion"] = "ALLOWED"
        with self.assertRaises(ValueError):
            self.verify(record)


if __name__ == "__main__":
    unittest.main()
