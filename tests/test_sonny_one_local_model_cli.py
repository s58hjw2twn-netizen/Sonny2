import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sonny_one.development_controller.local_model_cli import generate_review_proposal, main


class LocalModelCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "candidate.json"

    def test_requires_opt_in(self):
        with self.assertRaises(PermissionError):
            generate_review_proposal(model="local", output=self.output)

    def test_writes_review_only_artifact(self):
        class FakeAdapter:
            def __init__(self, producer):
                pass

            def propose(self, task):
                return {"task_id": "RES-001", "candidate_id": "a" * 64,
                        "patch_text": "test", "review_only": True,
                        "promotion": "FORBIDDEN"}
        with patch("sonny_one.development_controller.local_model_cli.ModelProposalAdapter",
                   FakeAdapter), patch(
                       "sonny_one.development_controller.local_model_cli.OllamaProposalProducer"):
            result = generate_review_proposal(
                model="local", output=self.output, enabled=True)
        artifact = json.loads(self.output.read_text())
        self.assertTrue(result["review_only"])
        self.assertFalse(artifact["approved_for_execution"])
        self.assertFalse(artifact["commit_created"])

    def test_existing_artifact_not_overwritten(self):
        self.output.write_text("preserve")
        with self.assertRaises(ValueError):
            generate_review_proposal(model="local", output=self.output, enabled=True)
        self.assertEqual(self.output.read_text(), "preserve")

    def test_symlink_output_rejected(self):
        original = Path(self.tmp.name) / "existing"
        original.write_text("secret")
        self.output.symlink_to(original)
        with self.assertRaises(ValueError):
            generate_review_proposal(model="local", output=self.output, enabled=True)

    def test_cli_disabled_exit_code(self):
        self.assertEqual(main(["--model", "local", "--output", str(self.output)]), 1)


if __name__ == "__main__":
    unittest.main()
