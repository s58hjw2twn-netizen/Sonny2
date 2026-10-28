import subprocess
import tempfile
import unittest
from pathlib import Path
from sonny_one.apl.patchcheck import check_generated


class PatchcheckTests(unittest.TestCase):
    def setup_repo(self, directory):
        root = Path(directory)
        path = root / "sonny_one/apl_targets/offline_strategy.py"
        path.parent.mkdir(parents=True)
        path.write_text(
            "def mean(values):\n    return sum(values) / len(values)\n"
            "def smallest(values):\n    return sorted(values)[0]\n"
            "def largest(values):\n    return max(values)\n", encoding="utf-8")
        for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Test",
                      "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")):
            subprocess.run(["git", *args], cwd=root, check=True,
                           capture_output=True)
        return root

    def test_disposable_applicability_without_source_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.setup_repo(tmp)
            before = (root / "sonny_one/apl_targets/offline_strategy.py").read_bytes()
            result = check_generated(root)
            self.assertEqual(len(result), 3)
            self.assertTrue(all(x["applicable_in_disposable_checkout"] for x in result))
            self.assertTrue(all(x["promotion"] == "FORBIDDEN" for x in result))
            self.assertEqual(before, (root / "sonny_one/apl_targets/offline_strategy.py").read_bytes())

    def test_dirty_checkout_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.setup_repo(tmp)
            (root / "untracked").write_text("dirty")
            with self.assertRaises(ValueError):
                check_generated(root)

    def test_non_git_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                check_generated(tmp)
