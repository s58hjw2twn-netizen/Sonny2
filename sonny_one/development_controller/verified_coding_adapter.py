"""Receipt-backed adapter for the Sonny ONE development controller.

A coding service supplies a proposed receipt; a separately trusted GitHub
reader validates commit ancestry and CI. No shell, network, model, or GitHub
write capability is embedded in this adapter. Do not share the coding
service's write credentials with the read-only verifier.
"""
from __future__ import annotations

from sonny_one.development_controller.github_verifier import verify_github_receipt


class VerifiedCodingAdapter:
    def __init__(self, *, produce_receipt, fetch_json, parent_sha: str,
                 repository: str = "s58hjw2twn-netizen/Sonny2"):
        if not callable(produce_receipt) or not callable(fetch_json):
            raise TypeError("coding producer and trusted GitHub reader are required")
        self.produce_receipt = produce_receipt
        self.fetch_json = fetch_json
        self.parent_sha = parent_sha
        self.repository = repository
        self.last_verification = None

    def __call__(self, task: dict) -> bool:
        if not isinstance(task, dict) or task.get("state") != "ready" or task.get("requires_approval") is not False:
            raise PermissionError("task not authorized")
        self.last_verification = None
        receipt = self.produce_receipt(dict(task))
        result = verify_github_receipt(
            receipt, expected_task_id=task["id"],
            expected_parent_sha=self.parent_sha,
            repository=self.repository, fetch_json=self.fetch_json,
        )
        if result.get("verified") is not True:
            return False
        self.last_verification = result
        self.parent_sha = result["commit_sha"]
        return True
