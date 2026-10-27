"""The signature verifier must fail closed when crypto is unavailable."""
import builtins
import unittest
from unittest.mock import patch
from sonny_one.apl.signed_holdout import verify_signed_external_holdout


class MissingCryptoTests(unittest.TestCase):
    def test_missing_dependency_rejects_unverified_result(self):
        original = builtins.__import__
        def unavailable(name, *args, **kwargs):
            if name.startswith("cryptography"):
                raise ImportError("cryptography unavailable")
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=unavailable):
            with self.assertRaisesRegex(RuntimeError, "dependency unavailable"):
                verify_signed_external_holdout(
                    dict(schema_version=1, candidate_sha256="a" * 64,
                         base_revision="b" * 40, evaluator_id="lab",
                         suite_sha256="c" * 64, result="PASS",
                         signature="placeholder"),
                    candidate_sha256="a" * 64, base_revision="b" * 40,
                    expected_evaluator="lab", trusted_public_key_pem="key")


if __name__ == "__main__":
    unittest.main()
