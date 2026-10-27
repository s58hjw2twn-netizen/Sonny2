"""Opt-in trusted Gemini transport for APL experimental patch proposals.

Invoke only outside the Docker candidate environment, with no repository write
token or private test fixtures. A provider request may be metered.
"""
import os
import re

from .model_intake import register_model_proposal

_SYSTEM = (
    "You propose one minimal unified git diff for an experimental Python target. "
    "Return only the diff beginning with diff --git, no markdown. "
    "Modify only the named target; never change tests, secrets, policies, or CI. "
    "You cannot see or run hidden tests. No claims about test results."
)


def propose_with_gemini(*, source_text, target_path, objective, base_revision,
                        predicted_pass=0.5, client=None):
    """Call existing Gemini transport from a trusted host, then validate output.

    Caller must supply a pinned base revision and nonsecret source snapshot.
    This function cannot execute, evaluate, commit, or promote patches.
    """
    from sonny.gemini_provider import generate_gemini

    if not isinstance(source_text, str) or not source_text or len(source_text.encode()) > 16000:
        raise ValueError("Source snapshot missing or exceeds 16KB")
    if not isinstance(target_path, str) or not re.fullmatch(
            r"sonny_one/apl_targets/[A-Za-z0-9_./-]+[.]py", target_path):
        raise ValueError("Only experimental Python targets allowed")
    if any(p in (".", "..", "") for p in target_path.split("/")):
        raise ValueError("Unsafe target path")
    if not isinstance(objective, str) or not 1 <= len(objective) <= 1000:
        raise ValueError("Invalid bounded objective")
    # Fail before any provider call on missing credentials or invalid revision.
    if not isinstance(base_revision, str) or not re.fullmatch(r"[0-9a-f]{40}", base_revision):
        raise ValueError("Pinned full base revision required")
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("Trusted host GEMINI_API_KEY is required")
    model = os.getenv("SONNY_GEMINI_MODEL", "gemini-2.5-flash")
    if not re.fullmatch(r"[A-Za-z0-9.-]{1,80}", model):
        raise ValueError("Invalid model identifier")
    prompt = ("Objective: " + objective + "\nTarget: " + target_path +
              "\nBase revision: " + base_revision + "\nSource snapshot:\n" + source_text)
    response = generate_gemini(_SYSTEM, [], prompt, client=client)
    if not isinstance(response, str) or len(response.encode()) > 128 * 1024:
        raise ValueError("Provider response exceeds patch budget")
    record = register_model_proposal({
        "model_id": "gemini/" + model,
        "patch_text": response,
        "predicted_pass": predicted_pass,
    }, base_revision=base_revision)
    if record["target_paths"] != [target_path]:
        raise ValueError("Provider changed an unauthorized target")
    record["provider_transport"] = "gemini_existing_trusted_host"
    record["provider_response_authenticated_by_transport"] = True
    # Provider transport authentication does not prove model identity or test quality.
    return record
