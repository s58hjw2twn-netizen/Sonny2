import unittest
from sonny_vision.proof_access import issue_proof_token, verify_proof_token


class ProofAccessTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * 32
        self.digest = "a" * 64
        self.token = issue_proof_token("job-1", "customer-1", self.digest,
                                       self.key, now=1000, ttl_seconds=300)

    def verify(self, token=None, job="job-1", customer="customer-1",
               digest=None, now=1100, key=None):
        return verify_proof_token(self.token if token is None else token,
                                  job, customer, self.digest if digest is None else digest,
                                  self.key if key is None else key, now)

    def test_valid_token(self):
        self.assertTrue(self.verify())

    def test_expired_token(self):
        self.assertFalse(self.verify(now=1300))

    def test_wrong_customer(self):
        self.assertFalse(self.verify(customer="customer-2"))

    def test_wrong_job(self):
        self.assertFalse(self.verify(job="job-2"))

    def test_wrong_proof_hash(self):
        self.assertFalse(self.verify(digest="b" * 64))

    def test_tampered_token(self):
        self.assertFalse(self.verify(token=self.token + "a"))

    def test_wrong_secret(self):
        self.assertFalse(self.verify(key=b"x" * 32))

    def test_invalid_lifetime_rejected(self):
        with self.assertRaises(ValueError):
            issue_proof_token("job-1", "customer-1", self.digest,
                              self.key, now=1000, ttl_seconds=7200)


if __name__ == "__main__":
    unittest.main()
