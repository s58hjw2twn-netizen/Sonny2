"""Cryptographic verification regression tests using ephemeral local test keys."""
import base64
import json
import unittest

from sonny_one.apl.signed_holdout import verify_signed_external_holdout

SHA = "a" * 64
REV = "b" * 40


class SignedHoldoutTests(unittest.TestCase):
    def setUp(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        self.record = dict(schema_version=1, candidate_sha256=SHA,
                           base_revision=REV, evaluator_id="isolated-lab",
                           suite_sha256="c" * 64, result="PASS")
        self.sign()

    def sign(self):
        canonical = json.dumps(self.record, sort_keys=True,
                               separators=(",", ":")).encode()
        self.signed = {**self.record,
                       "signature": base64.b64encode(self.key.sign(canonical)).decode()}

    def verify(self):
        return verify_signed_external_holdout(
            self.signed, candidate_sha256=SHA, base_revision=REV,
            expected_evaluator="isolated-lab", trusted_public_key_pem=self.public)

    def test_valid_signature_still_forbids_promotion(self):
        result = self.verify()
        self.assertTrue(result["signature_verified"])
        self.assertFalse(result["independent_custody_verified"])
        self.assertFalse(result["improvement_proven"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_tampered_result_rejected(self):
        self.signed["result"] = "FAIL"
        with self.assertRaises(ValueError):
            self.verify()

    def test_wrong_key_rejected(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        other = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        self.public = other
        with self.assertRaises(ValueError):
            self.verify()

    def test_invalid_base64_rejected(self):
        self.signed["signature"] = "not base64"
        with self.assertRaises(ValueError):
            self.verify()


if __name__ == "__main__":
    unittest.main()
