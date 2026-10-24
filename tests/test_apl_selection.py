import unittest
from sonny_one.apl.selection import select_for_review


def make_candidate(cid, delta=0.2):
    cycles = [{"candidate_id": cid, "cycle_id": f"c{i}",
               "mean_delta": delta, "bootstrap_95_percentile_interval": [0.01, 0.4],
               "review_recommended": True} for i in range(3)]
    return {"candidate_id": cid, "cycle_assessment": {
        "cycle_count": 3, "cycles": cycles, "all_cycles_positive": True,
        "human_review_recommended": True, "promotion": "FORBIDDEN",
        "improvement_proven": False, "recursive_improvement_proven": False}}


class SelectionTests(unittest.TestCase):
    def test_selects_highest_score_without_promotion(self):
        r = select_for_review([make_candidate("b", .2), make_candidate("a", .3)])
        self.assertEqual(r["selected_candidate_id"], "a")
        self.assertEqual(r["promotion"], "FORBIDDEN")

    def test_tie_break_is_deterministic(self):
        self.assertEqual(select_for_review([make_candidate("z"), make_candidate("a")])
                         ["selected_candidate_id"], "a")

    def test_duplicate_candidate_rejected(self):
        with self.assertRaises(ValueError):
            select_for_review([make_candidate("a"), make_candidate("a")])

    def test_spoofed_cycle_identity_rejected(self):
        c = make_candidate("a")
        c["cycle_assessment"]["cycles"][1]["candidate_id"] = "b"
        with self.assertRaises(ValueError):
            select_for_review([c])

    def test_spoofed_decision_rejected(self):
        c = make_candidate("a")
        c["cycle_assessment"]["cycles"][0]["review_recommended"] = False
        with self.assertRaises(ValueError):
            select_for_review([c])

    def test_no_positive_candidate(self):
        c = make_candidate("a")
        for item in c["cycle_assessment"]["cycles"]:
            item["mean_delta"] = 0
            item["bootstrap_95_percentile_interval"] = [0, 0]
            item["review_recommended"] = False
        c["cycle_assessment"]["all_cycles_positive"] = False
        c["cycle_assessment"]["human_review_recommended"] = False
        self.assertIsNone(select_for_review([c])["selected_candidate_id"])

    def test_rejects_claimed_proof(self):
        c = make_candidate("a")
        c["cycle_assessment"]["recursive_improvement_proven"] = True
        with self.assertRaises(ValueError):
            select_for_review([c])
