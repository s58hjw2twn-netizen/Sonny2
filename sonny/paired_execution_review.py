"""Compare externally recorded baseline and candidate command results.

Evidence is descriptive, not authenticated. This module never executes code,
approves commits, or treats caller-supplied results as independent verification.
"""

def summarize_pair(baseline: dict, candidate: dict) -> dict:
    def validate(record: dict) -> dict:
        if not isinstance(record, dict):
            raise ValueError("execution record must be a mapping")
        required = {"snapshot_sha256", "command_sha256", "exit_code", "stdout_sha256", "stderr_sha256"}
        if set(record) != required:
            raise ValueError("unexpected or missing execution evidence fields")
        for name in required - {"exit_code"}:
            value = record[name]
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("invalid evidence digest: " + name)
        if type(record["exit_code"]) is not int or not 0 <= record["exit_code"] <= 255:
            raise ValueError("invalid exit code")
        return record

    baseline = validate(baseline)
    candidate = validate(candidate)
    if baseline["command_sha256"] != candidate["command_sha256"]:
        raise ValueError("baseline and candidate commands differ")
    if baseline["snapshot_sha256"] == candidate["snapshot_sha256"]:
        raise ValueError("candidate must differ from baseline")
    return {
        "baseline_passed": baseline["exit_code"] == 0,
        "candidate_passed": candidate["exit_code"] == 0,
        "regression": baseline["exit_code"] == 0 and candidate["exit_code"] != 0,
        "candidate_snapshot_sha256": candidate["snapshot_sha256"],
        "evidence_authenticated": False,
        "independently_verified": False,
        "commit_allowed": False,
        "status": "UNTRUSTED_EXECUTION_RECORD_REVIEW",
    }
