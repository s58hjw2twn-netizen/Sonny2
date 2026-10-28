import unittest
from sonny_vision.identity.release_gate import restoration_release_gate

class StrictEvidenceTests(unittest.TestCase):
    def test_truthy_strings_do_not_approve(self):
        r=restoration_release_gate([{"geometry_pass":True}],identity_scores=[.99],
            texture_review_passed="yes",reference_review_passed="yes",owner_approved="yes")
        self.assertFalse(r["release_allowed"])
        self.assertIn("owner_approval_required",r["reasons"])

    def test_boolean_identity_score_is_invalid(self):
        r=restoration_release_gate([{"geometry_pass":True}],identity_scores=[True],
            texture_review_passed=True,reference_review_passed=True,owner_approved=True)
        self.assertFalse(r["release_allowed"])

    def test_boolean_threshold_rejected(self):
        with self.assertRaises(ValueError):
            restoration_release_gate([],min_identity_score=True)

    def test_valid_explicit_approvals(self):
        r=restoration_release_gate([{"geometry_pass":True}],identity_scores=[.99],
            texture_review_passed=True,reference_review_passed=True,owner_approved=True)
        self.assertTrue(r["release_allowed"])

if __name__=="__main__":
    unittest.main()
