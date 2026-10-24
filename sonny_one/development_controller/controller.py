"""Sonny ONE low-touch development controller (stdlib, offline, read-only).

Plans and validates the next task. Never edits code, invokes a model,
reads secrets, or deploys. An external authorized coding runner is required
for unattended implementation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ALLOWED_TRACKS = frozenset({"app", "research"})
ALLOWED_STATES = frozenset({"ready", "blocked", "done"})
APPROVAL_TERMS = ("deploy", "production", "merge main", "purchase", "paid api",
                  "secret", "credential", "private account", "frozen baseline")
MAX_TASKS = 200


def validate_queue(data: dict) -> list[dict]:
    if not isinstance(data, dict) or set(data) != {"version", "tasks"} or data["version"] != 1:
        raise ValueError("unsupported queue schema")
    tasks = data["tasks"]
    if not isinstance(tasks, list) or len(tasks) > MAX_TASKS:
        raise ValueError("invalid queue size")
    seen = set()
    for task in tasks:
        if not isinstance(task, dict) or set(task) != {"id", "track", "title", "state", "priority", "requires_approval"}:
            raise ValueError("invalid task fields")
        ident, title = task["id"], task["title"]
        if (not isinstance(ident, str) or not ident.isascii() or
            not 1 <= len(ident) <= 40 or
            not all(c.isalnum() or c in "-_" for c in ident) or ident in seen):
            raise ValueError("invalid or duplicate task id")
        seen.add(ident)
        if task["track"] not in ALLOWED_TRACKS or task["state"] not in ALLOWED_STATES:
            raise ValueError("invalid task track/state")
        if type(task["priority"]) is not int or not 1 <= task["priority"] <= 5:
            raise ValueError("invalid task priority")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
            raise ValueError("invalid task title")
        if type(task["requires_approval"]) is not bool:
            raise ValueError("approval must be boolean")
        if any(term in title.lower() for term in APPROVAL_TERMS) and not task["requires_approval"]:
            raise ValueError("approval-sensitive task must be gated")
    return tasks


def plan(data: dict) -> dict:
    tasks = validate_queue(data)
    available = [t for t in tasks if t["state"] == "ready" and not t["requires_approval"]]
    available.sort(key=lambda t: (t["priority"], t["track"], t["id"]))
    waiting = [t["id"] for t in tasks if t["state"] == "ready" and t["requires_approval"]]
    return {"next_task": available[0] if available else None,
            "ready_count": len(available), "approval_required": waiting,
            "execution_started": False, "coding_agent_connected": False,
            "autonomous_code_generation": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="sonny_one/development_controller/tasks.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--handoff", action="store_true", help="Generate non-authorizing coding-agent handoff")
    args = parser.parse_args()
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    if args.handoff:
        from sonny_one.development_controller.handoff import build_handoff
        result = build_handoff(queue)
    else:
        result = plan(queue)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
