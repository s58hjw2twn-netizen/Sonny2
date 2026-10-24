import tempfile
import unittest
from pathlib import Path

from sonny_one.apl.generator import generate_proposals
from sonny_one.apl.policy import validate_patch


SOURCE = """def mean(values):
    return sum(values) / len(values)

def smallest(values):
    return sorted(values)[0]

def largest(values):
    return max(values)
"""


class GeneratorTests(unittest.TestCase):
    def make_source(self, root):
        path = Path(root) / "sonny_one/apl_targets/offline_strategy.py"
        path.parent.mkdir(parents=True)
        path.write_text(SOURCE, encoding="utf-8")
        return path

    def test_bounded_deterministic_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_source(tmp)
            first = generate_proposals(tmp)
            self.assertEqual(first, generate_proposals(tmp))
            self.assertEqual(len(first), 3)
            for item in first:
                self.assertEqual(item["promotion"], "FORBIDDEN")
                self.assertIsNone(item["predicted_pass"])
                self.assertEqual(validate_patch(item["patch_text"]),
                                 ["sonny_one/apl_targets/offline_strategy.py"])

    def test_budget_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_source(tmp)
            self.assertEqual(len(generate_proposals(tmp, max_candidates=1)), 1)
            with self.assertRaises(ValueError):
                generate_proposals(tmp, max_candidates=4)

    def test_unlisted_target_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_source(tmp)
            with self.assertRaises(ValueError):
                generate_proposals(tmp, target="sonny/app.py")

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_source(tmp)
            actual = path.with_suffix(".real")
            path.rename(actual)
            path.symlink_to(actual)
            with self.assertRaises(ValueError):
                generate_proposals(tmp)

    def test_missing_target_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                generate_proposals(tmp)
