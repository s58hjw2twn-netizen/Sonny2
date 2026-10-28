import tempfile
import unittest
from pathlib import Path

from sonny_one.development_controller.coding_context import (
    TARGET, OBJECTIVE, build_coding_context, render_coding_prompt,
)


class CodingContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / TARGET
        self.target.parent.mkdir(parents=True)
        self.target.write_text("def mean(values):\n    return sum(values) / len(values)\n")

    def test_source_and_objective_in_prompt(self):
        context = build_coding_context(self.root)
        prompt = render_coding_prompt(context)
        self.assertIn("sum(values)", prompt)
        self.assertIn(OBJECTIVE, prompt)
        self.assertIn(TARGET, prompt)

    def test_source_fingerprint_mismatch(self):
        context = build_coding_context(self.root)
        context["source"] += "changed"
        with self.assertRaises(ValueError):
            render_coding_prompt(context)

    def test_reject_symlink_target(self):
        self.target.unlink()
        original = self.root / "other.py"
        original.write_text("secret")
        self.target.symlink_to(original)
        with self.assertRaises(ValueError):
            build_coding_context(self.root)

    def test_reject_oversize_source(self):
        self.target.write_bytes(b"x" * 8193)
        with self.assertRaises(ValueError):
            build_coding_context(self.root)

    def test_reject_changed_objective(self):
        context = build_coding_context(self.root)
        context["objective"] = "Modify authentication"
        with self.assertRaises(ValueError):
            render_coding_prompt(context)


if __name__ == "__main__":
    unittest.main()
