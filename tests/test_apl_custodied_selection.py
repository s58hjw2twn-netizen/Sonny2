import unittest
from sonny_one.apl.custody import seal_evidence
from sonny_one.apl.selection import select_custodied_for_review
from test_apl_verified_selection import build


KEY = b"k" * 32


def candidate():
    record = build("a")
    record["envelopes"] = [
        seal_evidence(c, KEY, custodian_id="independent")
        for c in record["raw_cycles"]
    ]
    return record


class CustodiedSelectionTests(unittest.TestCase):
    def test_verified_candidate_remains_review_only(self):
        result = select_custodied_for_review(
            [candidate()], KEY, expected_custodian="independent", resamples=100)
        self.assertTrue(result["custody_envelopes_verified"])
        self.assertEqual(result["selected_candidate_id"], "a")
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_score_tampering_rejected(self):
        record = candidate()
        record["raw_cycles"][0]["candidate_scores"]["t0"] = 0.0
        with self.assertRaises(ValueError):
            select_custodied_for_review(
                [record], KEY, expected_custodian="independent", resamples=100)

    def test_wrong_custodian_rejected(self):
        with self.assertRaises(ValueError):
            select_custodied_for_review(
                [candidate()], KEY, expected_custodian="attacker", resamples=100)

    def test_wrong_key_rejected(self):
        with self.assertRaises(ValueError):
            select_custodied_for_review(
                [candidate()], b"x" * 32, expected_custodian="independent",
                resamples=100)

    def test_missing_envelope_rejected(self):
        record = candidate()
        record["envelopes"].pop()
        with self.assertRaises(ValueError):
            select_custodied_for_review(
                [record], KEY, expected_custodian="independent", resamples=100)

    def test_replayed_envelope_rejected(self):
        record = candidate()
        record["raw_cycles"][1] = record["raw_cycles"][0]
        record["envelopes"][1] = record["envelopes"][0]
        with self.assertRaises(ValueError):
            select_custodied_for_review(
                [record], KEY, expected_custodian="independent", resamples=100)
