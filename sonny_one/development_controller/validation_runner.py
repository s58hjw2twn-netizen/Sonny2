"""Bounded offline validation runner for Sonny ONE.

Only runs hardcoded Python unittest commands. No user-supplied commands,
shell, network, credentials, model calls, code edits or deployment.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

COMMANDS = {
    "controller": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_sonny_one_development_controller.py", "-v"],
    "handoff": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_sonny_one_agent_handoff.py", "-v"],
    "runner_gate": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_sonny_one_runner_gate.py", "-v"],
    "preflight": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_sonny_one_runner_preflight.py", "-v"],
}
MAX_OUTPUT_CHARS = 12000


def execute_validation(name: str, timeout_seconds: int = 30) -> dict:
    if name not in COMMANDS:
        raise ValueError("validation is not on the immutable allowlist")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise ValueError("invalid timeout")
    started = time.monotonic()
    try:
        result = subprocess.run(
            COMMANDS[name], capture_output=True, text=True,
            timeout=timeout_seconds, check=False,
            stdin=subprocess.DEVNULL,
        )
        output = (result.stdout + "\n" + result.stderr)[-MAX_OUTPUT_CHARS:]
        return {"validation": name, "passed": result.returncode == 0,
                "return_code": result.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "output_tail": output, "code_changes_made": False,
                "autonomous_coding": False}
    except subprocess.TimeoutExpired:
        return {"validation": name, "passed": False, "return_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "output_tail": "Validation timed out",
                "code_changes_made": False, "autonomous_coding": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", choices=sorted(COMMANDS), required=True)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    report = execute_validation(args.validation, args.timeout)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
