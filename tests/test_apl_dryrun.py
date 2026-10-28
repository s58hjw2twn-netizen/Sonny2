import copy
import hashlib
import unittest

from sonny_one.apl.dryrun import inspect_bundle


PATCH = ("diff --git a/sonny_one/apl_targets/offline_strategy.py "
         "b/sonny_one/apl_targets/offline_strategy.py\n"
         "--- a/sonny_one/apl_targets/offline_strategy.py\n"
         "+++ b/sonny_one/apl_targets/offline_strategy.py\n"
         "@@ -1 +1 @@\n-old\n+new\n")


def fixture():
    digest = hashlib.sha256(PATCH.encode()).hexdigest()
    proposal = {"candidate_id": digest, "base_revision": "a" * 40,
                "patch_sha256": digest, "patch_text": PATCH,
                "changed_paths": ["sonny_one/apl_targets/offline_strategy.py"],
                "applicable_in_disposable_checkout": True,
                "predicted_pass": None, "candidate_code_executed": False,
                "promotion": "FORBIDDEN"}
    return {"format": "apl-offline-proposal-bundle-v1",
            "proposals": [proposal], "sandbox_execution_approved": False,
            "ready_for_runner": False, "promotion": "FORBIDDEN", "note": "offline"}


class DryRunTests(unittest.TestCase):
    def test_valid_bundle_stays_nonexecuting(self):
        result = inspect_bundle(fixture())
        self.assertTrue(result["schema_and_hashes_valid"])
        self.assertFalse(result["candidate_code_executed"])
        self.assertFalse(result["git_applicability_rechecked"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_tampered_patch_rejected(self):
        bundle = fixture()
        bundle["proposals"][0]["patch_text"] += "# modified\n"
        with self.assertRaises(ValueError):
            inspect_bundle(bundle)

    def test_tampered_candidate_identity_rejected(self):
        bundle = fixture()
        bundle["proposals"][0]["candidate_id"] = "0" * 64
        with self.assertRaises(ValueError):
            inspect_bundle(bundle)

    def test_unsafe_execution_flag_rejected(self):
        bundle = fixture()
        bundle["ready_for_runner"] = True
        with self.assertRaises(ValueError):
            inspect_bundle(bundle)

    def test_duplicate_candidate_rejected(self):
        bundle = fixture()
        bundle["proposals"].append(copy.deepcopy(bundle["proposals"][0]))
        with self.assertRaises(ValueError):
            inspect_bundle(bundle)

    def test_wrong_paths_rejected(self):
        bundle = fixture()
        bundle["proposals"][0]["changed_paths"] = ["sonny_one/production.py"]
        with self.assertRaises(ValueError):
            inspect_bundle(bundle)
