import unittest
from sonny_one.development_controller.github_verifier import verify_github_receipt

PARENT = "a" * 40
COMMIT = "b" * 40
REPO = "s58hjw2twn-netizen/Sonny2"


def fixture():
    receipt = {"task_id": "DEV-001", "parent_sha": PARENT,
               "commit_sha": COMMIT, "branch": "research/apl-001",
               "test_run_id": "101", "test_conclusion": "success",
               "policy_run_id": "102", "policy_conclusion": "success",
               "independent_verification": True}
    base = "https://api.github.com/repos/" + REPO
    records = {
        base + "/commits/" + COMMIT: {"sha": COMMIT, "parents": [{"sha": PARENT}]},
        base + "/actions/runs/101": {
            "id": 101, "head_sha": COMMIT, "head_branch": "research/apl-001",
            "name": "Sonny ONE Tests", "status": "completed", "conclusion": "success"},
        base + "/actions/runs/102": {
            "id": 102, "head_sha": COMMIT, "head_branch": "research/apl-001",
            "name": "APL experimental policy checks", "status": "completed",
            "conclusion": "success"},
    }
    return receipt, records, base


class GitHubVerifierTests(unittest.TestCase):
    def verify(self, receipt, records, repository=REPO):
        return verify_github_receipt(
            receipt, expected_task_id="DEV-001", expected_parent_sha=PARENT,
            repository=repository, fetch_json=lambda url: records[url])

    def test_matching_evidence(self):
        r, records, _ = fixture()
        self.assertTrue(self.verify(r, records)["verified"])

    def test_repository_restriction(self):
        r, records, _ = fixture()
        with self.assertRaises(ValueError):
            self.verify(r, records, "other/repo")

    def test_wrong_parent(self):
        r, records, base = fixture()
        records[base + "/commits/" + COMMIT]["parents"] = [{"sha": "c" * 40}]
        with self.assertRaises(ValueError):
            self.verify(r, records)

    def test_wrong_workflow(self):
        r, records, base = fixture()
        records[base + "/actions/runs/101"]["name"] = "pages build and deployment"
        with self.assertRaises(ValueError):
            self.verify(r, records)

    def test_wrong_head_sha(self):
        r, records, base = fixture()
        records[base + "/actions/runs/102"]["head_sha"] = PARENT
        with self.assertRaises(ValueError):
            self.verify(r, records)

    def test_pending_run(self):
        r, records, base = fixture()
        records[base + "/actions/runs/101"]["status"] = "in_progress"
        with self.assertRaises(ValueError):
            self.verify(r, records)

    def test_wrong_branch(self):
        r, records, base = fixture()
        records[base + "/actions/runs/102"]["head_branch"] = "main"
        with self.assertRaises(ValueError):
            self.verify(r, records)


if __name__ == "__main__":
    unittest.main()
