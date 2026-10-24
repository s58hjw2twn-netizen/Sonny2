"""Ephemeral, consent-gated memory prototype.

Research only: process-local RAM, no encryption, no persistence or network.
The caller MUST derive owner identity and authentication from a trusted session.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sonny_one.memory_consent_policy import authorize_memory_action


class EphemeralMemoryStore:
    def __init__(self):
        self._records: dict[str, tuple[str, str]] = {}

    def save(self, text: str, *, owner_id: str, owner_authenticated: bool,
             explicit_consent: bool, consent_expires_at: datetime,
             now: datetime | None = None) -> str:
        decision = authorize_memory_action(
            "save", owner_authenticated=owner_authenticated,
            explicit_consent=explicit_consent, owner_id=owner_id,
            memory_owner_id=owner_id, consent_expires_at=consent_expires_at,
            now=now,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        if not isinstance(text, str) or not text.strip() or len(text) > 500:
            raise ValueError("memory must contain 1-500 characters")
        record_id = uuid4().hex
        self._records[record_id] = (owner_id, text.strip())
        return record_id

    def recall(self, record_id: str, *, owner_id: str,
               owner_authenticated: bool, explicit_consent: bool,
               consent_expires_at: datetime, now: datetime | None = None) -> str:
        record = self._records.get(record_id)
        # Never disclose whether another owner's record exists.
        if record is None or record[0] != owner_id:
            raise KeyError("memory not found")
        decision = authorize_memory_action(
            "recall", owner_authenticated=owner_authenticated,
            explicit_consent=explicit_consent, owner_id=owner_id,
            memory_owner_id=record[0], consent_expires_at=consent_expires_at,
            now=now,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return record[1]

    def delete(self, record_id: str, *, owner_id: str,
               owner_authenticated: bool) -> None:
        record = self._records.get(record_id)
        if record is None or record[0] != owner_id:
            raise KeyError("memory not found")
        decision = authorize_memory_action(
            "delete", owner_authenticated=owner_authenticated,
            explicit_consent=False, owner_id=owner_id,
            memory_owner_id=record[0],
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        del self._records[record_id]

    def clear(self) -> None:
        """Drop all process-local records; does not guarantee physical RAM erasure."""
        self._records.clear()
