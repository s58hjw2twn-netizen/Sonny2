import json
import logging
import os

import httpx


CORE_VERSION = "1.2-conversation-history"

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

APPROVED LONG-TERM PROJECT MEMORY
{_memory_text(memories)}

MEMORY RULES
- Approved long-term memory is authoritative project memory.
- Conversation history is context, not automatically approved memory.
- Never claim that something from conversation history has been saved
  as long-term memory unless it appears in approved memory.
- If current conversation context conflicts with approved memory,
  identify the conflict instead of silently choosing one.

OPERATING RULES
- Help the user make useful progress toward the project's goal.
- Answer the user's actual question directly.
- Use relevant recent conversation context.
- Use approved project memory when relevant.
- Distinguish facts from assumptions and recommendations.
- State uncertainty when it materially affects the answer.
- Do not fabricate sources, memories, actions, or completed work.
- Correct false premises when necessary.
- Prefer concise, practical answers unless more detail is useful.
- When a concrete next action is appropriate, make it clear.
- Never claim consciousness, sentience, autonomous self-modification,
  or independent agency.
""".strip()


def _conversation_input(history, message):
    items = []

    for entry in history or []:
        role = entry.get("role")
        content = entry.get("content", "")

        if role not in {"user", "assistant"}:
            continue

        if not content:
            continue

        items.append({
            "role": role,
            "content": content
        })

    # The current user message may already have been stored before
    # respond() is called. Do not duplicate it if it is the last item.
    current_already_present = (
        items
        and items[-1]["role"] == "user"
        and items[-1]["content"] == message
    )

    if not current_already_present:
        items.append({
            "role": "user",
            "content": message
        })

    return items


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


def _call_openai(
    project,
    memories,
    history,
    message
):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    request_body = {
        "model": DEFAULT_MODEL,
        "instructions": _instructions(
            project,
            memories
        ),
        "input": _conversation_input(
            history,
            message
        ),
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
            error_body = response.text[:2000]

            logger.error(
                "OpenAI request failed: "
                "status=%s model=%s body=%s",
                response.status_code,
                DEFAULT_MODEL,
                error_body,
            )

            response.raise_for_status()

        payload = response.json()

    text = _extract_text(payload)

    if not text:
        logger.error(
            "OpenAI response contained no readable "
            "output text. model=%s",
            DEFAULT_MODEL,
        )

        raise RuntimeError(
            "OpenAI returned a response without "
            "readable output text"
        )

    return text


def _fallback(project):
    return (
        f"For {project['name']}, I couldn't reach the live AI model "
        f"right now. A useful next step is to clarify the next concrete "
        f"decision toward: {project['goal']}"
    )


def respond(
    project,
    memories,
    message,
    history=None
):
    try:
        text = _call_openai(
            project=project,
            memories=memories,
            history=history or [],
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
        logger.exception(
            "Unexpected Sonny model failure: %s",
            type(exc).__name__,
        )

    return {
        "text": _fallback(project),
        "answer_state": "FALLBACK",
        "memory_proposal": None,
    }
