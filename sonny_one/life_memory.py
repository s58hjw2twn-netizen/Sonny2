"""Consent-gated provenance-aware memory prototype; no production authentication."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from sonny_one.memory_policy import MemoryCandidate, MemoryStatus, admission_decision

@dataclass(frozen=True)
class MemoryRecord:
    id: int
    user_id: str
    statement: str
    source: str
    confidence: float
    valid_from: str
    valid_until: str | None

class LifeMemory:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS life_memory(
            id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, statement TEXT NOT NULL,
            source TEXT NOT NULL, confidence REAL NOT NULL, valid_from TEXT NOT NULL,
            valid_until TEXT, status TEXT NOT NULL, consent INTEGER NOT NULL)""")
        self.db.commit()

    def add(self, candidate: MemoryCandidate, *, valid_until: str | None = None) -> int:
        decision = admission_decision(candidate)
        if decision != "eligible-for-storage":
            raise ValueError(decision)
        if valid_until is not None:
            datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.db.execute("""INSERT INTO life_memory
            (user_id,statement,source,confidence,valid_from,valid_until,status,consent)
            VALUES(?,?,?,?,?,?,?,?)""",
            (candidate.user_id,candidate.statement,candidate.source,candidate.confidence,
             now,valid_until,candidate.status.value,int(candidate.consent)))
        self.db.commit()
        return int(cursor.lastrowid)

    def recall(self, user_id: str, *, at: datetime | None = None) -> list[MemoryRecord]:
        if not user_id:
            raise ValueError("user_id required")
        moment = (at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        rows = self.db.execute("""SELECT id,user_id,statement,source,confidence,valid_from,valid_until
            FROM life_memory WHERE user_id=? AND status='validated' AND consent=1
            AND valid_from<=? AND (valid_until IS NULL OR valid_until>?)
            ORDER BY id""", (user_id,moment,moment)).fetchall()
        return [MemoryRecord(*row) for row in rows]

    def revoke(self, user_id: str, memory_id: int) -> bool:
        cursor = self.db.execute("DELETE FROM life_memory WHERE id=? AND user_id=?", (memory_id,user_id))
        self.db.commit()
        return cursor.rowcount == 1

    def erase_user(self, user_id: str) -> None:
        if not user_id:
            raise ValueError("user_id required")
        self.db.execute("DELETE FROM life_memory WHERE user_id=?", (user_id,))
        self.db.commit()
