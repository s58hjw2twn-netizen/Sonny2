"""Read-only GitHub Actions verification for Sonny ONE development receipts.

The injected fetch_json function must use an authenticated, trusted GitHub API
transport. This module makes no network calls or writes by itself.
"""
from __future__ import annotations

from sonny_one.development_controller.execution_receipt import validate_execution_receipt


def verify_github_receipt(receipt: dict, *, expected_task_id: str,
                          expected_parent_sha: str, repository: str,
                          fetch_json) -> dict:
    if repository != "s58hjw2twn-netizen/Sonny2":
        raise ValueError("repository not allowlisted")
    # First validate shape; the flag is not accepted as independent evidence.
    validate_execution_receipt(receipt, expected_task_id=expected_task_id,
                               expected_parent_sha=expected_parent_sha)
    base = "https://api.github.com/repos/" + repository
    commit = fetch_json(base + "/commits/" + receipt["commit_sha"])
    if not isinstance(commit, dict) or commit.get("sha") != receipt["commit_sha"]:
        raise ValueError("commit not found")
    parents = commit.get("parents", [])
    if not isinstance(parents, list) or not any(
        isinstance(p, dict) and p.get("sha") == expected_parent_sha for p in parents
    ):
        raise ValueError("commit parent mismatch")
    for key, workflow in (
        ("test_run_id", "Sonny ONE Tests"),
        ("policy_run_id", "APL experimental policy checks"),
    ):
        run = fetch_json(base + "/actions/runs/" + receipt[key])
        if (not isinstance(run, dict) or run.get("id") != int(receipt[key])
                or run.get("head_sha") != receipt["commit_sha"]
                or run.get("head_branch") != "research/apl-001"
                or run.get("name") != workflow
                or run.get("status") != "completed"
                or run.get("conclusion") != "success"):
            raise ValueError("GitHub workflow evidence mismatch")
    return {"verified": True, "commit_sha": receipt["commit_sha"],
            "task_id": expected_task_id, "source": "trusted_github_api"}
