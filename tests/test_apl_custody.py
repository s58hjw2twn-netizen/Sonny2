import unittest
from sonny_one.apl.custody import seal_evidence, verify_evidence


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * 32
        self.record = {"candidate_id": "abc", "score": 0.5, "suite_sha256": "f" * 64}
        self.envelope = seal_evidence(self.record, self.key, custodian_id="offline")

    def test_roundtrip(self):
        self.assertTrue(verify_evidence(self.record, self.envelope, self.key,
                                        expected_custodian="offline"))

    def test_modified_score_rejected(self):
        self.assertFalse(verify_evidence({**self.record, "score": 0.9},
                                         self.envelope, self.key,
                                         expected_custodian="offline"))

    def test_wrong_key_rejected(self):
        self.assertFalse(verify_evidence(self.record, self.envelope, b"x" * 32,
                                         expected_custodian="offline"))

    def test_wrong_custodian_rejected(self):
        self.assertFalse(verify_evidence(self.record, self.envelope, self.key,
                                         expected_custodian="attacker"))

    def test_tampered_mac_rejected(self):
        bad = dict(self.envelope, mac_sha256="0" * 64)
        self.assertFalse(verify_evidence(self.record, bad, self.key,
                                         expected_custodian="offline"))

    def test_weak_key_rejected(self):
        with self.assertRaises(ValueError):
            seal_evidence(self.record, b"short", custodian_id="offline")

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            seal_evidence({"score": float("nan")}, self.key, custodian_id="offline")
