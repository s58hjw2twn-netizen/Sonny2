"""Deterministic regression tests for the research-only RES-001 change."""
import unittest

from sonny_one.apl_targets.offline_strategy import largest, mean, smallest


class RES001RegressionTests(unittest.TestCase):
    def test_nonempty_mean(self):
        self.assertEqual(mean([2, 4, 6]), 4)
        self.assertEqual(mean((1, 2)), 1.5)

    def test_empty_mean_rejected(self):
        for values in ([], ()):
            with self.subTest(values=values), self.assertRaises(ValueError):
                mean(values)

    def test_other_functions_unchanged(self):
        self.assertEqual(smallest([9, 2, 4]), 2)
        self.assertEqual(largest([9, 2, 4]), 9)


if __name__ == "__main__":
    unittest.main()
