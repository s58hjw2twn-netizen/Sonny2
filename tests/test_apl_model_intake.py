"""Offline tests for untrusted model proposal intake; no model or Docker required."""
import unittest
from unittest.mock import patch

from sonny_one.apl.model_intake import register_model_proposal, evaluate_model_proposals


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

    def test_model_queue_registers_provenance_before_evaluation(self):
        events = []
        def append(ledger, record):
            events.append(("lineage", record))
        def queue(manifest, **kwargs):
            events.append(("queue", manifest))
            self.assertEqual(len(manifest), 1)
            with open(manifest[0]["patch"], encoding="utf-8") as handle:
                self.assertEqual(handle.read(), PATCH)
            return {"attempted": 1, "promotion": "FORBIDDEN"}
        with patch("sonny_one.apl.policy.append_lineage", side_effect=append), \\
             patch("sonny_one.apl.loop.run_queue", side_effect=queue):
            result = evaluate_model_proposals(
                [proposal()], revision=REV, ledger="/tmp/apl-test-ledger.jsonl")
        self.assertEqual(result["promotion"], "FORBIDDEN")
        self.assertEqual(events[0][0], "lineage")
        self.assertFalse(events[0][1]["model_identity_authenticated"])
        self.assertEqual(events[1][0], "queue")

    def test_invalid_batch_never_reaches_queue(self):
        with patch("sonny_one.apl.loop.run_queue") as queue, \\
             patch("sonny_one.apl.policy.append_lineage") as ledger:
            with self.assertRaises(ValueError):
                evaluate_model_proposals([proposal(), proposal(model_id="bad id")],
                                         revision=REV, ledger="/tmp/apl-test-ledger.jsonl")
            queue.assert_not_called()
            ledger.assert_not_called()

    def test_requires_immutable_base_revision(self):
        with self.assertRaises(ValueError):
            register_model_proposal(proposal(), base_revision="main")


if __name__ == "__main__":
    unittest.main()
