import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sonny_one.apl.package import prepare_bundle, write_bundle


class BundleTests(unittest.TestCase):
    def make_repo(self, root):
        path = Path(root) / "sonny_one/apl_targets/offline_strategy.py"
        path.parent.mkdir(parents=True)
        path.write_text("def mean(values):\n    return sum(values) / len(values)\n",
                        encoding="utf-8")
        for args in (("init", "-q"), ("add", "."),
                     ("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                      "commit", "-qm", "fixture")):
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    def test_bundle_is_review_only_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_repo(tmp)
            a = prepare_bundle(tmp)
            b = prepare_bundle(tmp)
            self.assertEqual(a, b)
            self.assertFalse(a["ready_for_runner"])
            self.assertFalse(a["sandbox_execution_approved"])
            self.assertEqual(a["promotion"], "FORBIDDEN")
            self.assertIsNone(a["proposals"][0]["predicted_pass"])
            self.assertFalse(a["proposals"][0]["candidate_code_executed"])

    def test_bundle_is_create_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self.make_repo(repo)
            bundle = prepare_bundle(repo)
            target = Path(tmp) / "bundle.json"
            digest = write_bundle(bundle, target)
            self.assertEqual(len(digest), 64)
            self.assertEqual(json.loads(target.read_text()), bundle)
            with self.assertRaises(FileExistsError):
                write_bundle(bundle, target)

    def test_dirty_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_repo(tmp)
            (Path(tmp) / "dirty.txt").write_text("x")
            with self.assertRaises(ValueError):
                prepare_bundle(tmp)
