"""Validate model-proposed patches before any staging or execution.

The model is untrusted. This gate does not contact a model, write files,
run code, or authorize commits.
"""
import hashlib
import ast

MAX_PATCH_BYTES = 32_000
ALLOWED_PREFIXES = ("sonny/", "tests/")
PROTECTED_FILES = frozenset({
    "sonny/model_patch_gate.py",
    "sonny/candidate_stager.py",
    "sonny/research_agent.py",
    "sonny/isolated_test_command.py",
    "sonny/isolated_syntax_executor.py",
    "sonny/paired_syntax_runner.py",
    "sonny/paired_execution_review.py",
    "sonny/candidate_evaluator.py",
})


def validate_model_patch(proposal: dict) -> dict:
    if not isinstance(proposal, dict) or set(proposal) != {"path", "content", "reason"}:
        raise ValueError("invalid model patch schema")
    path, content, reason = proposal["path"], proposal["content"], proposal["reason"]
    if not isinstance(path, str) or not path.startswith(ALLOWED_PREFIXES):
        raise ValueError("patch path not allowlisted")
    if (path.startswith("/") or "\\" in path or
            any(part in ("", ".", "..") for part in path.split("/")) or
            not path.endswith(".py") or path.startswith("tests/__")):
        raise ValueError("unsafe patch path")
    if (path in PROTECTED_FILES or path.startswith(("sonny/security_", "sonny/auth", "sonny/model_", "sonny/isolated_", "sonny/paired_", "sonny/candidate_", "sonny/research_", "tests/test_model_", "tests/test_candidate_", "tests/test_research_", "tests/test_isolated_", "tests/test_paired_"))):
        raise ValueError("model cannot modify research safety controls")
    if not isinstance(content, str) or not isinstance(reason, str):
        raise ValueError("invalid patch fields")
    try:
        encoded = content.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("proposal content must be valid UTF-8") from exc
    if not encoded or len(encoded) > MAX_PATCH_BYTES or "\x00" in content:
        raise ValueError("invalid patch size or content")
    if not reason.strip() or len(reason) > 500:
        raise ValueError("invalid patch rationale")
    try:
        ast.parse(content, filename=path)
    except (SyntaxError, ValueError) as exc:
        raise ValueError("proposal is not syntactically valid Python") from exc
    return {
        "path": path,
        "content_sha256": hashlib.sha256(encoded).hexdigest(),
        "content_bytes": len(encoded),
        "approved_for_staging": False,
        "commit_allowed": False,
        "status": "MODEL_PATCH_VALIDATED_NOT_APPROVED",
    }


def validate_scoped_model_patch(proposal: dict, allowed_paths: tuple[str, ...]) -> dict:
    """Validate an untrusted proposal against an independently supplied task scope."""
    result = validate_model_patch(proposal)
    if not isinstance(allowed_paths, tuple) or not allowed_paths:
        raise ValueError("task scope required")
    if result["path"] not in allowed_paths:
        raise ValueError("proposal outside approved task scope")
    return result


def stage_scoped_model_patch(task, files: dict[str, str], proposal: dict) -> dict:
    """Stage a whole-file model proposal in memory; never write or execute it."""
    from sonny.candidate_stager import Replacement, stage_candidate
    from sonny.research_agent import validate_task

    validate_task(task)
    if task.risk != "low":
        raise ValueError("only low-risk model tasks can be staged")
    validated = validate_scoped_model_patch(proposal, task.paths)
    path = validated["path"]
    if not isinstance(files, dict) or path not in files:
        raise ValueError("target must exist in snapshot")
    original = files[path]
    if not isinstance(original, str) or not original:
        raise ValueError("target must contain text")
    replacement = proposal["content"]
    if replacement == original:
        raise ValueError("model proposal makes no change")
    if len(original.encode()) + len(replacement.encode()) > MAX_PATCH_BYTES:
        raise ValueError("whole-file replacement exceeds staging budget")
    staged = stage_candidate(task, files, [Replacement(path, original, replacement)])
    staged["model_proposal_sha256"] = validated["content_sha256"]
    staged["commit_allowed"] = False
    return staged
