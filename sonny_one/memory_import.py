"""Validate and atomically import user-approved portable memory snapshots.

Caller must authenticate the destination user and explicitly obtain consent.
Plaintext snapshots must be handled securely. No API or filesystem I/O here.
"""
from datetime import datetime, timezone
import json
import math
from sonny_one.memory_export import FORMAT, VERSION

def import_active_memories(memory, user_id: str, payload: str, *, consent: bool) -> int:
    if not isinstance(user_id, str) or not user_id.strip() or consent is not True:
        raise ValueError("Authenticated destination user and consent required")
    if not isinstance(payload, str) or len(payload.encode("utf-8")) > 2_000_000:
        raise ValueError("Invalid or oversized snapshot")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("Nonstandard JSON number")

    data = json.loads(payload, object_pairs_hook=unique_object,
                      parse_constant=reject_constant)
    if (not isinstance(data, dict) or set(data) != {"format", "version", "records"}
            or data["format"] != FORMAT or type(data["version"]) is not int
            or data["version"] != VERSION or not isinstance(data["records"], list)
            or len(data["records"]) > 10_000):
        raise ValueError("Unsupported snapshot")
    now = datetime.now(timezone.utc)
    validated = []
    for record in data["records"]:
        if (not isinstance(record, dict)
                or set(record) != {"statement", "source", "confidence", "valid_until"}):
            raise ValueError("Invalid record schema")
        statement = record["statement"]
        source = record["source"]
        confidence = record["confidence"]
        expiry = record["valid_until"]
        if (not isinstance(statement, str) or not statement.strip()
                or len(statement) > 10_000 or not isinstance(source, str)
                or not source.strip() or len(source) > 1000
                or type(confidence) not in (float, int)
                or not math.isfinite(confidence) or not 0 <= confidence <= 1):
            raise ValueError("Invalid memory values")
        if expiry is not None:
            if not isinstance(expiry, str):
                raise ValueError("Invalid expiration")
            until = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if until.tzinfo is None or until.astimezone(timezone.utc) <= now:
                raise ValueError("Expired or timezone-naive record")
        validated.append((user_id, statement, source, confidence,
                          now.isoformat(), expiry, "validated", 1))
    # All validation precedes database writes. SQLite context commits or rolls back.
    with memory.db:
        memory.db.executemany(
            """INSERT INTO life_memory
            (user_id,statement,source,confidence,valid_from,valid_until,status,consent)
            VALUES(?,?,?,?,?,?,?,?)""", validated)
    return len(validated)
