"""Regression tests for causal held-out comparison."""
import unittest
from sonny_one.causal_holdout import compare_holdout

class HoldoutTests(unittest.TestCase):
    def test_better(self):
        r = compare_holdout([0.9]*20, [0.1]*20, [False]*20)
        self.assertEqual(r["direction"], "candidate_better_descriptively")
    def test_small_sample(self):
        self.assertEqual(compare_holdout([0.9], [0.1], [False])["direction"], "insufficient_evidence")
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            compare_holdout([float("nan")], [0.5], [True])
    def test_nonboolean_rejected(self):
        with self.assertRaises(ValueError):
            compare_holdout([0.5], [0.5], [1])
    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            compare_holdout([0.5], [0.5, 0.5], [True])
    def test_tie(self):
        self.assertEqual(compare_holdout([0.5]*20, [0.5]*20, [True]*20)["direction"], "tied")
    def test_never_applies_changes(self):
        self.assertFalse(compare_holdout([0.5], [0.1], [True])["changes_applied"])
