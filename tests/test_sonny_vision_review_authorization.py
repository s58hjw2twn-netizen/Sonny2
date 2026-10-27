import unittest
from sonny_vision.restoration.review_authorization import sign_review, verify_review

class ReviewAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.secret=b"private-demo-secret-material-32-bytes-minimum"
        self.record={"reviewer_id":"reviewer-1","reviewer_confirmed":True,
          "source_sha256":"a"*64,"proposal_sha256":"b"*64,
          "decisions":[{"id":"C1","decision":"reject"}]}
    def sign(self):
        self.record["authorization_hmac_sha256"]=sign_review(self.record,self.secret)
    def test_signed_record(self):
        self.sign()
        self.assertTrue(verify_review(self.record,self.secret,expected_reviewer_id="reviewer-1"))
    def test_changed_vote_rejected(self):
        self.sign()
        self.record["decisions"][0]["decision"]="approve"
        with self.assertRaises(ValueError): verify_review(self.record,self.secret)
    def test_changed_source_rejected(self):
        self.sign()
        self.record["source_sha256"]="c"*64
        with self.assertRaises(ValueError): verify_review(self.record,self.secret)
    def test_missing_signature_rejected(self):
        with self.assertRaises(ValueError): verify_review(self.record,self.secret)
    def test_wrong_secret_rejected(self):
        self.sign()
        with self.assertRaises(ValueError): verify_review(self.record,b"x"*32)
    def test_reviewer_mismatch_rejected(self):
        self.sign()
        with self.assertRaises(ValueError): verify_review(self.record,self.secret,expected_reviewer_id="other")
    def test_short_secret_rejected(self):
        with self.assertRaises(ValueError): sign_review(self.record,b"short")
