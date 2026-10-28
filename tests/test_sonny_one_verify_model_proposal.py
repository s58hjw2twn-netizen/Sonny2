import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sonny_one.development_controller.verify_model_proposal import verify_proposal


class ModelProposalVerificationTests(unittest.TestCase):
    def test_rejects_stale_source_before_patch_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "proposal.json"
            artifact.write_text(json.dumps({
                "format": "sonny-one-review-only-model-proposal-v1",
                "approved_for_execution": False, "commit_created": False,
                "baseline_sha256": "0" * 64,
                "proposal": {"task_id": "RES-001", "patch_text": "not a patch"},
            }))
            with patch("sonny_one.development_controller.verify_model_proposal.build_coding_context",
                       return_value={"source_sha256": "1" * 64, "source": "safe"}):
                with self.assertRaisesRegex(ValueError, "stale baseline"):
                    verify_proposal(artifact, Path(directory))

    def test_rejects_artifact_claiming_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "proposal.json"
            artifact.write_text(json.dumps({
                "format": "sonny-one-review-only-model-proposal-v1",
                "approved_for_execution": False, "commit_created": True,
                "proposal": {"task_id": "RES-001", "patch_text": "patch"},
            }))
            with self.assertRaisesRegex(ValueError, "review-only"):
                verify_proposal(artifact, Path(directory))


if __name__ == "__main__":
    unittest.main()
