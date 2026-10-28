import unittest

from sonny_one.development_controller.static_acceptance import check_mean_change

BASE = '''def mean(values):
    return sum(values) / len(values)


def smallest(values):
    return sorted(values)[0]


def largest(values):
    return max(values)
'''
GOOD = BASE.replace('    return sum(values) / len(values)',
                    '    if not values:\n        raise ValueError("empty")\n    return sum(values) / len(values)')


class StaticAcceptanceTests(unittest.TestCase):
    def test_good_candidate(self):
        result = check_mean_change(BASE, GOOD)
        self.assertTrue(result["static_checks_passed"])
        self.assertFalse(result["candidate_executed"])

    def test_missing_value_error(self):
        with self.assertRaises(ValueError):
            check_mean_change(BASE, BASE)

    def test_rejects_unrelated_function_change(self):
        changed = GOOD.replace("return max(values)", "return min(values)")
        with self.assertRaises(ValueError):
            check_mean_change(BASE, changed)

    def test_rejects_removed_sum(self):
        with self.assertRaises(ValueError):
            check_mean_change(BASE, GOOD.replace("sum(values)", "max(values)"))

    def test_rejects_top_level_side_effect(self):
        with self.assertRaises(ValueError):
            check_mean_change(BASE, GOOD + '\nprint("side effect")\n')

    def test_rejects_top_level_import(self):
        with self.assertRaises(ValueError):
            check_mean_change(BASE, 'import os\n' + GOOD)

    def test_rejects_unapproved_call(self):
        with self.assertRaises(ValueError):
            check_mean_change(BASE, GOOD.replace('raise ValueError("empty")',
                                                 'print("leak")\n        raise ValueError("empty")'))

    def test_rejects_bad_syntax(self):
        with self.assertRaises(SyntaxError):
            check_mean_change(BASE, "def mean(")


if __name__ == "__main__":
    unittest.main()
