import unittest

from sonny_one.causal_evidence import make_receipt, verify_receipt


class EvidenceTests(unittest.TestCase):
    def test_exact_match(self):
        r = make_receipt("t1", "local-test", b"pass")
        self.assertTrue(verify_receipt(r, "t1", b"pass"))
        self.assertFalse(r.authenticated)

    def test_tamper_rejected(self):
        r = make_receipt("t1", "local-test", b"pass")
        self.assertFalse(verify_receipt(r, "t1", b"fail"))

    def test_wrong_task_rejected(self):
        r = make_receipt("t1", "local-test", b"pass")
        self.assertFalse(verify_receipt(r, "t2", b"pass"))

    def test_empty_payload_rejected(self):
        with self.assertRaises(ValueError):
            make_receipt("t1", "local-test", b"")

    def test_bad_input_rejected(self):
        self.assertFalse(verify_receipt(None, "t1", b"pass"))


if __name__ == "__main__":
    unittest.main()
