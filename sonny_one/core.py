"""Minimal auditable Sonny ONE research foundation. No autonomous deployment or model-weight changes."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import json
import sqlite3

@dataclass(frozen=True)
class Identity:
    agent_id: str = "sonny-one-research"
    version: str = "0.1.0"
    purpose: str = "Assist people while remaining correctable and under human control"

@dataclass
class EmotionalSimulation:
    curiosity: float = 0.5
    caution: float = 0.5
    engagement: float = 0.5

    def update(self, *, uncertainty: float, novelty: float) -> None:
        self.caution = max(0.0, min(1.0, uncertainty))
        self.curiosity = max(0.0, min(1.0, novelty))
        self.engagement = max(0.0, min(1.0, (self.curiosity + 1 - self.caution) / 2))

class MemoryStore:
    """Explicit, per-user SQLite event memory with provenance and consent."""
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            content TEXT NOT NULL,
            provenance TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.db.commit()

    def remember(self, user_id: str, kind: str, content: dict[str, Any], provenance: str, *, consent: bool = False) -> int:
        if not consent:
            raise PermissionError("Explicit consent required for persistent memory")
        if not user_id or not provenance:
            raise ValueError("user_id and provenance required")
        cursor = self.db.execute(
            "INSERT INTO memories(user_id,kind,content,provenance,created_at) VALUES (?,?,?,?,?)",
            (user_id, kind, json.dumps(content), provenance, datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return int(cursor.lastrowid)

    def recall(self, user_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT kind,content,provenance FROM memories WHERE user_id=? ORDER BY id", (user_id,)).fetchall()
        return [{"kind": k, "content": json.loads(c), "provenance": p} for k,c,p in rows]

    def forget(self, user_id: str) -> None:
        self.db.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
        self.db.commit()

@dataclass(frozen=True)
class Candidate:
    identifier: str
    evidence_score: float
    independent_evaluation: bool = False
    human_approved: bool = False

class BoundedRSI:
    """Decision gate only: never executes candidate code or changes deployments."""
    def evaluate(self, candidate: Candidate) -> str:
        if not 0 <= candidate.evidence_score <= 1:
            return "reject-invalid-score"
        if not candidate.independent_evaluation:
            return "hold-independent-evaluation"
        if candidate.evidence_score < 0.8:
            return "reject-insufficient-evidence"
        if not candidate.human_approved:
            return "hold-human-approval"
        return "eligible-for-manual-review"
