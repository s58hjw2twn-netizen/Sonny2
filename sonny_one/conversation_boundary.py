"""Fail-closed request data limits for Sonny ONE private assistant routes.

Pure local validation; no persistence, external model calls or network access.
Designed for integration before a future private conversation store.
"""
from __future__ import annotations


def validate_conversation_payload(message: str, memories: list[str], *,
                                  max_total_chars: int = 12000, goal: str = "") -> dict:
    if type(max_total_chars) is not int or not 1 <= max_total_chars <= 12000:
        raise ValueError("invalid payload budget")
    if not isinstance(message, str) or not message.strip() or len(message) > 4000:
        raise ValueError("message must contain 1-4000 characters")
    if not isinstance(memories, list) or len(memories) > 50:
        raise ValueError("memory list exceeds limit")
    if any(not isinstance(m, str) or not m.strip() or len(m) > 500
           for m in memories):
        raise ValueError("invalid approved memory")
    if not isinstance(goal, str) or len(goal) > 500:
        raise ValueError("invalid goal")
    # Reject control characters other than ordinary whitespace; avoid invisible
    # payload delimiters reaching logs, UI, or a future model adapter.
    fields = [message, goal, *memories]
    if any(any(ord(ch) < 32 and ch not in "\\t\\n\\r" for ch in value)
           or "\\x7f" in value for value in fields):
        raise ValueError("control characters are not permitted")
    total = len(message) + len(goal) + sum(len(m) for m in memories)
    if total > max_total_chars:
        raise ValueError("conversation payload budget exceeded")
    return {"message": message.strip(), "goal": goal.strip(), "memories": list(memories),
            "total_chars": total, "persistent_storage_authorized": False,
            "external_provider_authorized": False}
