"""Offline tests for untrusted model proposal intake; no model or Docker required."""
import unittest

from sonny_one.apl.model_intake import register_model_proposal


REV = "a" * 40
PATCH = ("diff --git a/sonny_one/apl_targets/offline_strategy.py "
         "b/sonny_one/apl_targets/offline_strategy.py\n"
         "--- a/sonny_one/apl_targets/offline_strategy.py\n"
         "+++ b/sonny_one/apl_targets/offline_strategy.py\n"
         "@@ -1 +1 @@\n-old\n+new\n")


def proposal(**changes):
    data = {"model_id": "provider/model-v1", "patch_text": PATCH,
            "predicted_pass": 0.75}
    data.update(changes)
    return data


class ModelIntakeTests(unittest.TestCase):
    def test_valid_proposal_remains_review_only(self):
        result = register_model_proposal(proposal(), base_revision=REV)
        self.assertEqual(result["candidate_id"], result["patch_sha256"])
        self.assertEqual(result["base_revision"], REV)
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertFalse(result["tests_executed"])
        self.assertFalse(result["model_identity_authenticated"])
        self.assertFalse(result["improvement_proven"])

    def test_rejects_non_experimental_path(self):
        with self.assertRaises(ValueError):
            register_model_proposal(proposal(
                patch_text=PATCH.replace("sonny_one/apl_targets/offline_strategy.py",
                                         "sonny/app.py")), base_revision=REV)

    def test_rejects_invalid_probability_and_metadata(self):
        for data in (proposal(predicted_pass=float("nan")),
                     proposal(predicted_pass=True),
                     proposal(model_id="model;rm -rf /"),
                     dict(proposal(), claimed_tests_passed=True)):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    register_model_proposal(data, base_revision=REV)

    def test_requires_immutable_base_revision(self):
        with self.assertRaises(ValueError):
            register_model_proposal(proposal(), base_revision="main")


if __name__ == "__main__":
    unittest.main()
