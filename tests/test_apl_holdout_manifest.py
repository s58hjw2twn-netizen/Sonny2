"""Trusted holdout manifest hashing and fail-closed intake."""
import hashlib
import unittest
from sonny_one.apl.holdout_manifest import (
    canonical_request_sha256, create_holdout_request,
)


class HoldoutManifestTests(unittest.TestCase):
    def test_candidate_digest_and_deterministic_manifest(self):
        a = create_holdout_request(b"patch-data", base_revision="b" * 40,
                                   suite_sha256="c" * 64)
        self.assertEqual(a["candidate_sha256"],
                         hashlib.sha256(b"patch-data").hexdigest())
        self.assertEqual(canonical_request_sha256(a),
                         canonical_request_sha256(dict(reversed(list(a.items())))))

    def test_empty_and_oversized_candidates_rejected(self):
        for candidate in (b"", b"x" * (2 * 1024 * 1024 + 1), "not bytes"):
            with self.subTest(size=len(candidate)), self.assertRaises(ValueError):
                create_holdout_request(candidate, base_revision="b" * 40,
                                       suite_sha256="c" * 64)

    def test_invalid_manifest_rejected(self):
        good = create_holdout_request(b"patch", base_revision="b" * 40,
                                      suite_sha256="c" * 64)
        for changes in ({"base_revision": "invalid"},
                        {"suite_sha256": "invalid"},
                        {"candidate_sha256": "invalid"},
                        {"unexpected": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                canonical_request_sha256({**good, **changes})


if __name__ == "__main__":
    unittest.main()
