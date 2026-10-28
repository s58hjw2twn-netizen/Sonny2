import unittest

from sonny_one.causal_self_model import CausalSelfModel
from sonny_one.causal_evidence import make_receipt
from sonny_one.causal_review_gate import ReviewedOutcome, record_reviewed_outcome


class CausalReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.model = CausalSelfModel({"test": True})
        self.model.predict("t1", "test", 0.75, "baseline")
        self.receipt = make_receipt("t1", "local-test", b"test passed")
        self.trusted = frozenset({"reviewer-a"})

    def review(self, **overrides):
        data = dict(task_id="t1", succeeded=True, reviewer_id="reviewer-a",
                    receipt=self.receipt)
        data.update(overrides)
        return ReviewedOutcome(**data)

    def test_reviewed_outcome_recorded(self):
        record_reviewed_outcome(self.model, self.review(), b"test passed",
                                trusted_reviewers=self.trusted)
        self.assertEqual(self.model.report()["observed"], 1)

    def test_untrusted_reviewer_rejected(self):
        with self.assertRaises(PermissionError):
            record_reviewed_outcome(self.model, self.review(reviewer_id="stranger"),
                                    b"test passed", trusted_reviewers=self.trusted)

    def test_tampering_rejected(self):
        with self.assertRaises(ValueError):
            record_reviewed_outcome(self.model, self.review(), b"test failed",
                                    trusted_reviewers=self.trusted)

    def test_wrong_task_rejected(self):
        with self.assertRaises(ValueError):
            record_reviewed_outcome(self.model, self.review(task_id="t2"),
                                    b"test passed", trusted_reviewers=self.trusted)

    def test_duplicate_outcome_rejected(self):
        record_reviewed_outcome(self.model, self.review(), b"test passed",
                                trusted_reviewers=self.trusted)
        with self.assertRaises(ValueError):
            record_reviewed_outcome(self.model, self.review(), b"test passed",
                                    trusted_reviewers=self.trusted)

    def test_fake_authenticated_flag_rejected(self):
        from dataclasses import replace
        forged = replace(self.receipt, authenticated=True)
        with self.assertRaises(ValueError):
            record_reviewed_outcome(self.model, self.review(receipt=forged),
                                    b"test passed", trusted_reviewers=self.trusted)


if __name__ == "__main__":
    unittest.main()
