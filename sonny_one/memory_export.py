"""Versioned, user-scoped memory export. No file or network access."""
import json

FORMAT = "sonny-one-memory"
VERSION = 1

def export_active_memories(memory, user_id: str) -> str:
    """Export approved, active records for a caller-authenticated user.

    The caller must authenticate the user and protect the plaintext result.
    """
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id required")
    records = memory.recall(user_id)
    if len(records) > 10000:
        raise ValueError("too many records")
    payload = {
        "format": FORMAT,
        "version": VERSION,
        "records": [
            {"statement": item.statement, "source": item.source,
             "confidence": item.confidence, "valid_until": item.valid_until}
            for item in records
        ],
    }
    result = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if len(result.encode("utf-8")) > 2000000:
        raise ValueError("export exceeds size limit")
    return result
