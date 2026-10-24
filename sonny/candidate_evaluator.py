"""Independent, side-effect-free candidate evaluation.

This evaluator checks the exact staged fingerprint and compares an explicit
set of deterministic checks. It does NOT run tests or commit code.
"""
import hashlib
import ast


def fingerprint(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode() + bytes([0]))
        digest.update(files[path].encode() + bytes([0]))
    return digest.hexdigest()


def evaluate_candidate(staged: dict, baseline_checks: dict[str, bool],
                       candidate_checks: dict[str, bool]) -> dict:
    if staged.get("status") != "STAGED_FOR_INDEPENDENT_TESTING":
        raise ValueError("candidate is not staged")
    files = staged.get("candidate")
    if not isinstance(files, dict) or not files:
        raise ValueError("candidate snapshot missing")
    if fingerprint(files) != staged.get("sha256"):
        raise ValueError("candidate fingerprint mismatch")
    if not baseline_checks or set(baseline_checks) != set(candidate_checks):
        raise ValueError("checks must be paired and nonempty")
    if not all(isinstance(x, bool) for x in baseline_checks.values()):
        raise ValueError("baseline checks must be boolean")
    if not all(isinstance(x, bool) for x in candidate_checks.values()):
        raise ValueError("candidate checks must be boolean")
    regressions = sorted(
        name for name in baseline_checks
        if baseline_checks[name] and not candidate_checks[name]
    )
    failures = sorted(name for name, passed in candidate_checks.items() if not passed)
    return {
        "task_id": staged["task_id"],
        "candidate_sha256": staged["sha256"],
        "regressions": regressions,
        "failed_checks": failures,
        "passed": not failures and not regressions,
        "status": "EVIDENCE_REVIEW_ONLY",
        "commit_allowed": False,
        "tests_executed_by_evaluator": 0,
    }


def check_python_syntax(staged: dict) -> dict:
    """Parse changed Python files without executing candidate source."""
    if staged.get("status") != "STAGED_FOR_INDEPENDENT_TESTING":
        raise ValueError("candidate not staged")
    files = staged.get("candidate")
    if not isinstance(files, dict) or not files:
        raise ValueError("candidate snapshot missing")
    if fingerprint(files) != staged.get("sha256"):
        raise ValueError("candidate fingerprint mismatch")
    paths = staged.get("changed_paths")
    if not isinstance(paths, list) or not paths:
        raise ValueError("changed paths missing")
    checks = {}
    for path in paths:
        if not isinstance(path, str) or not path.endswith(".py") or path not in files:
            raise ValueError("syntax check requires staged Python files")
        try:
            ast.parse(files[path], filename=path)
        except (SyntaxError, ValueError, TypeError):
            checks[path] = False
        else:
            checks[path] = True
    return {
        "candidate_sha256": staged["sha256"],
        "checks": checks,
        "all_passed": all(checks.values()),
        "candidate_code_executed": False,
        "commit_allowed": False,
    }
