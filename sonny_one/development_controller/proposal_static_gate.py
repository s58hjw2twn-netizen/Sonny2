"""Evaluate an untrusted model diff without executing candidate code.

Use a bounded unified diff parser to reconstruct the one allowlisted source
file in memory. This is a review gate, not git apply, a sandbox, or a test run.
"""
from __future__ import annotations

import re

from sonny_one.apl.policy import validate_patch
from sonny_one.development_controller.coding_context import TARGET
from sonny_one.development_controller.static_acceptance import check_mean_change

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)?$")
MAX_SOURCE_BYTES = 8192


def reconstruct_candidate(before: str, patch_text: str) -> str:
    if not isinstance(before, str) or len(before.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("invalid baseline source")
    if validate_patch(patch_text) != [TARGET]:
        raise ValueError("candidate must change exactly the research target")
    original = before.splitlines(keepends=True)
    if not before.endswith("\n"):
        raise ValueError("baseline must end with newline")
    lines = patch_text.splitlines()
    if len(lines) < 4 or lines[0] != f"diff --git a/{TARGET} b/{TARGET}":
        raise ValueError("invalid diff header")
    index = 1
    if lines[index].startswith("index "):
        index += 1
    if lines[index:index + 2] != [f"--- a/{TARGET}", f"+++ b/{TARGET}"]:
        raise ValueError("invalid file headers")
    index += 2
    cursor = 0
    output = []
    hunks = 0
    while index < len(lines):
        match = _HUNK.fullmatch(lines[index])
        if not match:
            raise ValueError("unexpected patch content")
        old_start = int(match.group(1))
        old_count = int(match.group(2) or 1)
        new_count = int(match.group(4) or 1)
        if old_start < 1 or old_start - 1 < cursor or old_start - 1 > len(original):
            raise ValueError("invalid or overlapping hunk")
        output.extend(original[cursor:old_start - 1])
        cursor = old_start - 1
        index += 1
        consumed = produced = 0
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if not line or line[0] not in " +-":
                raise ValueError("invalid hunk line")
            payload = line[1:] + "\n"
            if line[0] in " -":
                if cursor >= len(original) or original[cursor] != payload:
                    raise ValueError("patch does not match baseline")
                cursor += 1
                consumed += 1
            if line[0] in " +":
                output.append(payload)
                produced += 1
            index += 1
        if consumed != old_count or produced != new_count:
            raise ValueError("hunk line counts mismatch")
        hunks += 1
    if hunks == 0:
        raise ValueError("no patch hunks")
    output.extend(original[cursor:])
    result = "".join(output)
    if len(result.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("candidate source too large")
    return result


def evaluate_static_proposal(before: str, patch_text: str) -> dict:
    after = reconstruct_candidate(before, patch_text)
    result = check_mean_change(before, after)
    return {**result, "applicability_checked_in_memory": True,
            "git_apply_checked": False, "candidate_executed": False,
            "independent_tests_passed": False}
