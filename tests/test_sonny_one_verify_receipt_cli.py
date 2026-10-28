import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sonny_one.development_controller.verify_receipt_cli import check_receipt_file, main

PARENT = "a" * 40
COMMIT = "b" * 40
BASE = "https://api.github.com/repos/s58hjw2twn-netizen/Sonny2"


def receipt():
    return {"task_id": "DEV-001", "parent_sha": PARENT, "commit_sha": COMMIT,
            "branch": "research/apl-001", "test_run_id": "101",
            "test_conclusion": "success", "policy_run_id": "102",
            "policy_conclusion": "success", "independent_verification": True}


def fetch(url):
    records = {
        BASE + "/commits/" + COMMIT: {"sha": COMMIT, "parents": [{"sha": PARENT}]},
        BASE + "/branches/research/apl-001": {"commit": {"sha": COMMIT}},
        BASE + "/actions/runs/101": {
            "id": 101, "head_sha": COMMIT, "head_branch": "research/apl-001",
            "name": "Sonny ONE Tests", "status": "completed", "conclusion": "success"},
        BASE + "/actions/runs/102": {
            "id": 102, "head_sha": COMMIT, "head_branch": "research/apl-001",
            "name": "APL experimental policy checks", "status": "completed",
            "conclusion": "success"},
    }
    return records[url]


class ReceiptCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "receipt.json"
        self.path.write_text(json.dumps(receipt()), encoding="utf-8")

    def test_valid_end_to_end_mock_github(self):
        result = check_receipt_file(self.path, task_id="DEV-001",
                                    parent_sha=PARENT, fetch_json=fetch)
        self.assertTrue(result["verified"])

    def test_reject_wrong_parent(self):
        with self.assertRaises(ValueError):
            check_receipt_file(self.path, task_id="DEV-001",
                               parent_sha="c" * 40, fetch_json=fetch)

    def test_reject_oversized_file(self):
        self.path.write_bytes(b" " * 8193)
        with self.assertRaises(ValueError):
            check_receipt_file(self.path, task_id="DEV-001",
                               parent_sha=PARENT, fetch_json=fetch)

    def test_reject_symlink(self):
        link = Path(self.tmp.name) / "link.json"
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            check_receipt_file(link, task_id="DEV-001",
                               parent_sha=PARENT, fetch_json=fetch)

    def test_reject_invalid_task_id(self):
        with self.assertRaises(ValueError):
            check_receipt_file(self.path, task_id="../other",
                               parent_sha=PARENT, fetch_json=fetch)

    def test_cli_failure_exit(self):
        with patch("sonny_one.development_controller.verify_receipt_cli.check_receipt_file",
                   side_effect=ValueError("invalid")):
            self.assertEqual(main(["--receipt", str(self.path), "--task-id", "DEV-001",
                                   "--parent-sha", PARENT]), 1)


if __name__ == "__main__":
    unittest.main()
