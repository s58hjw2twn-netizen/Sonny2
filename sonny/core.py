import json
import logging
import os

import httpx


CORE_VERSION = "1.1-model-backed-diagnostic"

OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.getenv("SONNY_MODEL", "gpt-5.4-mini")

logger = logging.getLogger("sonny.core")


def _memory_text(memories):
    if not memories:
        return "No approved memories are currently available."

    approved = []

    for memory in memories:
        value = memory.get("value")

        if value:
            approved.append(f"- {value}")

    if not approved:
        return "No approved memories are currently available."

    return "\n".join(approved)


def _instructions(project, memories):
    project_name = project.get("name", "Sonny Project")
    project_goal = project.get("goal", "")

    return f"""
You are Sonny, the AI Project Co-Pilot for this project.

PROJECT
Name: {project_name}
Goal: {project_goal}

APPROVED PROJECT MEMORY
{_memory_text(memories)}

OPERATING RULES
- Help the user make useful progress toward the project's goal.
- Answer the user's actual question directly.
- Use approved project memory when relevant.
- Do not claim to remember information that is not in approved memory
  or the current conversation.
- Distinguish facts from assumptions and recommendations.
- State uncertainty when it materially affects the answer.
- Do not fabricate sources, memories, actions, or completed work.
- Correct false premises when necessary.
- Prefer concise, practical answers unless more detail is useful.
- When a concrete next action is appropriate, make it clear.
- Never claim consciousness, sentience, autonomous self-modification,
  or independent agency.
""".strip()


def _extract_text(payload):
    if payload.get("output_text"):
        return payload["output_text"].strip()

    pieces = []

    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text")

                if text:
                    pieces.append(text)

    return "\n".join(pieces).strip()


def _call_openai(project, memories, message):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    request_body = {
        "model": DEFAULT_MODEL,
        "instructions": _instructions(project, memories),
        "input": message,
        "max_output_tokens": 1200,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            OPENAI_API_URL,
            headers=headers,
            json=request_body,
        )

        if response.is_error:
            # Safe diagnostic:
            # logs OpenAI's status/error response but never the API key.
            error_body = response.text[:2000]

            logger.error(
                "OpenAI request failed: status=%s model=%s body=%s",
                response.status_code,
                DEFAULT_MODEL,
                error_body,
            )

            response.raise_for_status()

        payload = response.json()

    text = _extract_text(payload)

    if not text:
        logger.error(
            "OpenAI response contained no readable output text. model=%s",
            DEFAULT_MODEL,
        )

        raise RuntimeError(
            "OpenAI returned a response without readable output text"
        )

    return text


def _fallback(project):
    return (
        f"For {project['name']}, I couldn't reach the live AI model "
        f"right now. A useful next step is to clarify the next concrete "
        f"decision toward: {project['goal']}"
    )


def respond(project, memories, message):
    try:
        text = _call_openai(
            project=project,
            memories=memories,
            message=message,
        )

        return {
            "text": text,
            "answer_state": "MODEL",
            "memory_proposal": None,
        }

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Sonny model HTTP failure: status=%s",
            exc.response.status_code,
        )

    except httpx.RequestError as exc:
        logger.error(
            "Sonny model network failure: %s",
            type(exc).__name__,
        )

    except json.JSONDecodeError:
        logger.error(
            "Sonny model returned invalid JSON."
        )

    except RuntimeError as exc:
        logger.error(
            "Sonny model runtime failure: %s",
            str(exc),
        )

    except Exception as exc:
        # Do not expose request headers or secrets.
        logger.exception(
            "Unexpected Sonny model failure: %s",
            type(exc).__name__,
        )

    return {
        "text": _fallback(project),
        "answer_state": "FALLBACK",
        "memory_proposal": None,
    }
