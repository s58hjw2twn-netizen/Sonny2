import unittest
from sonny_vision.identity.release_gate import restoration_release_gate

class ReleaseGateTests(unittest.TestCase):
    def test_missing_evidence_fails_closed(self):
        self.assertFalse(restoration_release_gate([])["release_allowed"])

    def test_multiple_faces_all_required(self):
        reports = [{"geometry_pass": True}, {"geometry_pass": False}]
        result = restoration_release_gate(reports, identity_scores=[0.95, 0.95],
            texture_review_passed=True, reference_review_passed=True, owner_approved=True)
        self.assertFalse(result["release_allowed"])

    def test_all_gates_allow_provisional_release(self):
        result = restoration_release_gate([{"geometry_pass": True}], identity_scores=[0.95],
            texture_review_passed=True, reference_review_passed=True, owner_approved=True)
        self.assertTrue(result["release_allowed"])
        self.assertTrue(result["threshold_provisional"])

    def test_nonfinite_score_rejected(self):
        self.assertFalse(restoration_release_gate([{"geometry_pass": True}],
            identity_scores=[float("nan")])["release_allowed"])

if __name__ == "__main__":
    unittest.main()
