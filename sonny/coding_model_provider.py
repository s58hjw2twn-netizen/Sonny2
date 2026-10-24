"""Bounded coding-model adapter for the existing Gemini transport.

Opt-in only: calling this function may make a metered provider request.
No model credentials, Git writes, shell commands, or deployment here.
"""
from .gemini_provider import generate_gemini
from .model_patch_gate import stage_model_response

INSTRUCTIONS = """You are an untrusted coding assistant.
Return ONLY one JSON object with exactly three keys: path, content, reason.
The path must be the exact requested existing Python file.
The content must be the entire updated Python file, not a diff.
Do not add markdown fences or explanatory text.
Never modify security controls, test harnesses, or unrelated files.
Keep the change minimal and explain it briefly in reason.
"""


def generate_and_stage_patch(task, files: dict[str, str], *, client=None) -> dict:
    """Generate one patch with Gemini, validate and stage in memory only.

    The caller must explicitly invoke this function with server-side credentials.
    There is no automatic retry, commit, filesystem write, or code execution.
    """
    from .research_agent import validate_task

    validate_task(task)
    if task.risk != "low" or len(task.paths) != 1:
        raise ValueError("coding model requires one low-risk target")
    path = task.paths[0]
    if not isinstance(files, dict) or path not in files:
        raise ValueError("target file missing from snapshot")
    original = files[path]
    if not isinstance(original, str) or not original:
        raise ValueError("target file must contain text")
    if len(original.encode("utf-8")) > 16_000:
        raise ValueError("source file exceeds coding-model input budget")
    prompt = (
        "Task: " + task.objective + "\n"
        "Target path: " + path + "\n"
        "Existing source:\n" + original
    )
    response = generate_gemini(INSTRUCTIONS, [], prompt, client=client)
    staged = stage_model_response(task, files, response)
    staged["provider"] = "gemini"
    staged["independently_verified"] = False
    staged["commit_allowed"] = False
    return staged
