"""Offline coding-runner preflight. Does not launch an autonomous coding agent.

A real coding runner must independently authenticate approvals, provision a
sandbox and least-privilege credentials, and run only on a dedicated branch.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sonny_one.development_controller.handoff import build_handoff
from sonny_one.development_controller.runner_gate import runner_available


def preflight(queue: dict) -> dict:
    handoff = build_handoff(queue)
    return {
        "handoff": handoff,
        "runner_connected": runner_available(),
        "can_start_unattended": False,
        "reason": "No independently authenticated, sandboxed coding runner is configured",
        "next_setup_steps": [
            "Select an approved coding runner and determine its usage limits",
            "Provision isolated development branch and least-privilege credentials",
            "Verify sandbox, network restrictions, and credential boundaries",
            "Require signed authorization and independent CI evidence before code promotion",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="sonny_one/development_controller/tasks.json")
    args = parser.parse_args()
    data = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    print(json.dumps(preflight(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
