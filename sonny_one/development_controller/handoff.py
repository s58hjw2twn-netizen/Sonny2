"""Strict, read-only coding-agent handoff generation.

The resulting JSON is an instruction *proposal*, not an authorization token.
A separately reviewed runner must authenticate its source and enforce its own
sandbox, permissions, spending and branch controls.
"""
from __future__ import annotations

from sonny_one.development_controller.controller import plan

ALLOWED_BRANCH = "research/apl-001"


def build_handoff(queue: dict) -> dict:
    selection = plan(queue)
    task = selection["next_task"]
    return {
        "schema_version": 1,
        "repository": "s58hjw2twn-netizen/Sonny2",
        "branch": ALLOWED_BRANCH,
        "task": (
            {"id": task["id"], "track": task["track"],
             "title": task["title"], "priority": task["priority"]}
            if task else None
        ),
        "mode": "proposal_only",
        "execution_authorized": False,
        "write_credentials_provided": False,
        "network_access_authorized": False,
        "paid_services_authorized": False,
        "merge_authorized": False,
        "deployment_authorized": False,
        "secret_access_authorized": False,
        "frozen_research_mutation_authorized": False,
        "required_evidence": ["targeted_tests", "full_ci", "commit_sha",
                              "change_summary", "approval_boundary_check"],
        "owner_approval_required": selection["approval_required"],
    }
