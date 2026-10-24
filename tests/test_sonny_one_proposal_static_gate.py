import unittest

from sonny_one.development_controller.coding_context import TARGET
from sonny_one.development_controller.proposal_static_gate import (
    evaluate_static_proposal, reconstruct_candidate,
)

BASE = ('def mean(values):\n'
        '    return sum(values) / len(values)\n'
        '\n\n'
        'def smallest(values):\n'
        '    return sorted(values)[0]\n'
        '\n\n'
        'def largest(values):\n'
        '    return max(values)\n')
HEADER = (f'diff --git a/{TARGET} b/{TARGET}\n'
          f'--- a/{TARGET}\n'
          f'+++ b/{TARGET}\n')
HUNK = ('@@ -1,2 +1,4 @@\n'
        ' def mean(values):\n'
        '+    if not values:\n'
        '+        raise ValueError("empty")\n'
        '     return sum(values) / len(values)\n')


class ProposalStaticGateTests(unittest.TestCase):
    def test_valid_in_memory_patch(self):
        result = evaluate_static_proposal(BASE, HEADER + HUNK)
        self.assertTrue(result["static_checks_passed"])
        self.assertFalse(result["candidate_executed"])
        self.assertFalse(result["git_apply_checked"])

    def test_rejects_truncated_patch(self):
        with self.assertRaises(ValueError):
            reconstruct_candidate(BASE, (HEADER + HUNK).rstrip("\\n"))

    def test_rejects_nontext_patch(self):
        with self.assertRaises(ValueError):
            reconstruct_candidate(BASE, None)

    def test_rejects_wrong_context(self):
        bad = HUNK.replace(" def mean(values):", " def other(values):")
        with self.assertRaises(ValueError):
            reconstruct_candidate(BASE, HEADER + bad)

    def test_rejects_wrong_counts(self):
        with self.assertRaises(ValueError):
            reconstruct_candidate(BASE, HEADER + HUNK.replace("+1,4", "+1,5"))

    def test_rejects_unexpected_patch_command(self):
        with self.assertRaises(ValueError):
            reconstruct_candidate(BASE, HEADER + HUNK + "shell command\n")

    def test_rejects_missing_hunks(self):
        with self.assertRaises(ValueError):
            reconstruct_candidate(BASE, HEADER)

    def test_rejects_unrelated_function_change(self):
        bad = ('@@ -8,2 +8,2 @@\n'
               ' def largest(values):\n'
               '-    return max(values)\n'
               '+    return min(values)\n')
        with self.assertRaises(ValueError):
            evaluate_static_proposal(BASE, HEADER + HUNK + bad)


if __name__ == "__main__":
    unittest.main()
