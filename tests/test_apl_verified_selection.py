import copy
import unittest
from sonny_one.apl.metrics import compare_metrics
from sonny_one.apl.cycles import assess_cycles
from sonny_one.apl.selection import select_verified_for_review


def build(cid):
    raw = []
    for i in range(3):
        baseline = {f"t{j}": 0.0 for j in range(20)}
        candidate = {f"t{j}": 1.0 for j in range(20)}
        evaluation = {"status": "ELIGIBLE_FOR_HUMAN_REVIEW",
                      "candidate_id": f"{cid}-{i}", "base_revision": "base",
                      "lineage_hash": f"hash-{cid}-{i}"}
        attachment = {"local_lineage_verified": True,
                      "runner_status": evaluation["status"],
                      "candidate_id": evaluation["candidate_id"],
                      "base_revision": "base", "lineage_hash": evaluation["lineage_hash"],
                      "promotion": "FORBIDDEN", "improvement_proven": False,
                      "grader": "external", "metrics": compare_metrics(baseline, candidate)}
        raw.append({"cycle_id": f"cycle-{i}", "suite_fingerprint": f"{i+1:064x}",
                    "evaluation": evaluation, "attachment": attachment,
                    "baseline_scores": baseline, "candidate_scores": candidate})
    return {"candidate_id": cid, "raw_cycles": raw,
            "cycle_assessment": assess_cycles(raw, resamples=100)}


class VerifiedSelectionTests(unittest.TestCase):
    def test_verified_raw_evidence_selects_review_only(self):
        r = select_verified_for_review([build("a")], resamples=100)
        self.assertEqual(r["selected_candidate_id"], "a")
        self.assertTrue(r["raw_evidence_recomputed"])
        self.assertEqual(r["promotion"], "FORBIDDEN")

    def test_fabricated_positive_summary_rejected(self):
        c = build("a")
        c["cycle_assessment"]["cycles"][0]["mean_delta"] = 0.99
        with self.assertRaises(ValueError):
            select_verified_for_review([c], resamples=100)

    def test_changed_raw_scores_rejected(self):
        c = build("a")
        c["raw_cycles"][0]["candidate_scores"]["t0"] = 0.0
        with self.assertRaises(ValueError):
            select_verified_for_review([c], resamples=100)

    def test_wrong_bootstrap_seed_rejected(self):
        c = build("a")
        with self.assertRaises(ValueError):
            select_verified_for_review([c], resamples=100, seed=99)

    def test_missing_raw_evidence_rejected(self):
        c = build("a")
        del c["raw_cycles"]
        with self.assertRaises(ValueError):
            select_verified_for_review([c], resamples=100)
