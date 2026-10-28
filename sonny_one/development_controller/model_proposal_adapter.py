"""Strict adapter boundary for an optional external coding model.

The adapter accepts structured proposals, not shell commands. It does not
invoke a model, write files, execute code, or grant repository permissions.
Untrusted proposals must still pass independent patch policy and sandbox
review before any application.
"""
from __future__ import annotations

import hashlib

from sonny_one.apl.policy import validate_patch

MAX_PATCH_BYTES = 32768
ALLOWED_TASKS = frozenset({"RES-001"})


def validate_model_proposal(task: dict, proposal: dict) -> dict:
    if not isinstance(task, dict) or task.get("id") not in ALLOWED_TASKS:
        raise PermissionError("task not allowlisted for model proposals")
    if task.get("state") != "ready" or task.get("requires_approval") is not False:
        raise PermissionError("task not authorized")
    if not isinstance(proposal, dict) or set(proposal) != {"task_id", "patch_text"}:
        raise ValueError("proposal schema mismatch")
    if proposal["task_id"] != task["id"]:
        raise ValueError("proposal task mismatch")
    patch_text = proposal["patch_text"]
    if not isinstance(patch_text, str) or not patch_text:
        raise ValueError("missing patch")
    data = patch_text.encode("utf-8")
    if len(data) > MAX_PATCH_BYTES:
        raise ValueError("proposal exceeds size budget")
    changed_paths = validate_patch(patch_text)
    if changed_paths != ["sonny_one/apl_targets/offline_strategy.py"]:
        raise ValueError("model proposal changes a path outside its exact allowlist")
    return {"task_id": task["id"],
            "candidate_id": hashlib.sha256(data).hexdigest(),
            "patch_text": patch_text, "review_only": True,
            "code_executed": False, "committed": False,
            "promotion": "FORBIDDEN"}


class ModelProposalAdapter:
    def __init__(self, model_producer):
        if not callable(model_producer):
            raise TypeError("model producer must be callable")
        self.model_producer = model_producer
        self.last_proposal = None

    def propose(self, task: dict) -> dict:
        if not isinstance(task, dict) or task.get("id") not in ALLOWED_TASKS:
            raise PermissionError("task not allowlisted")
        if task.get("state") != "ready" or task.get("requires_approval") is not False:
            raise PermissionError("task not authorized")
        proposal = self.model_producer(dict(task))
        self.last_proposal = validate_model_proposal(task, proposal)
        return self.last_proposal

    def __call__(self, task: dict) -> bool:
        self.propose(task)
        return False
