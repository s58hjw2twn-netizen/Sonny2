import unittest

from sonny.research_agent import Task
from sonny.candidate_stager import Replacement, stage_candidate
from sonny.rsi_candidate_review import review_candidate_experiment, review_replication_records


class CombinedReviewTests(unittest.TestCase):
    def setUp(self):
        self.staged = stage_candidate(
            Task("rsi-review", "Change a constant", ("sonny/sample.py",)),
            {"sonny/sample.py": "value = 1\n"},
            [Replacement("sonny/sample.py", "value = 1", "value = 2")],
        )
        self.manifest = {
            "benchmark_id": "frozen-test",
            "cases": ["a", "b"],
            "minimum_gain": 0.1,
            "maximum_regressions": 0,
            "fixture_sha256": "a" * 64,
        }

    def review(self, checks=None, scores=None):
        return review_candidate_experiment(
            self.staged, {"syntax": True},
            {"syntax": True} if checks is None else checks,
            self.manifest, {"a": 0.5, "b": 0.5},
            {"a": 0.8, "b": 0.8} if scores is None else scores,
        )

    def test_good_claims_still_cannot_authorize_commit(self):
        result = self.review()
        self.assertTrue(result["eligible_for_independent_replication"])
        self.assertFalse(result["independently_verified"])
        self.assertFalse(result["commit_allowed"])
        self.assertFalse(result["promotion_allowed"])

    def test_code_failure_blocks_replication(self):
        result = self.review(checks={"syntax": False})
        self.assertFalse(result["eligible_for_independent_replication"])

    def test_benchmark_failure_blocks_replication(self):
        result = self.review(scores={"a": 0.5, "b": 0.5})
        self.assertFalse(result["eligible_for_independent_replication"])

    def test_tampered_snapshot_fails_closed(self):
        self.staged["candidate"]["sonny/sample.py"] = "value = 999\n"
        with self.assertRaises(ValueError):
            self.review()

    def test_replication_record_matches_candidate_but_stays_unverified(self):
        review = self.review()
        base = dict(snapshot_sha256="b" * 64, command_sha256="c" * 64,
                    exit_code=0, stdout_sha256="d" * 64, stderr_sha256="e" * 64)
        candidate = dict(base, snapshot_sha256=review["candidate_sha256"])
        result = review_replication_records(review, base, candidate)
        self.assertTrue(result["execution_records_consistent"])
        self.assertFalse(result["independently_verified"])
        self.assertFalse(result["commit_allowed"])

    def test_replication_record_wrong_candidate_digest_rejected(self):
        review = self.review()
        base = dict(snapshot_sha256="b" * 64, command_sha256="c" * 64,
                    exit_code=0, stdout_sha256="d" * 64, stderr_sha256="e" * 64)
        candidate = dict(base, snapshot_sha256="f" * 64)
        with self.assertRaises(ValueError):
            review_replication_records(review, base, candidate)

    def test_failed_preliminary_review_blocks_replication(self):
        review = self.review(scores={"a": 0.5, "b": 0.5})
        with self.assertRaises(ValueError):
            review_replication_records(review, {}, {})


if __name__ == "__main__":
    unittest.main()
