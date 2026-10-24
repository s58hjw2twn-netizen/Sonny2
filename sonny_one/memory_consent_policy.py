"""Pure, offline consent policy for proposed Sonny ONE private memory.

This module deliberately stores nothing and never handles encryption keys.
It must not be represented as an encrypted memory store.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Literal


class MemoryAction(str, Enum):
    SAVE = "save"
    RECALL = "recall"
    DELETE = "delete"


@dataclass(frozen=True)
class ConsentDecision:
    allowed: bool
    action: str
    reason: str
    storage_performed: bool = False


def authorize_memory_action(
    action: Literal["save", "recall", "delete"],
    *,
    owner_authenticated: bool,
    explicit_consent: bool,
    owner_id: str,
    memory_owner_id: str,
    consent_expires_at: datetime | None = None,
    now: datetime | None = None,
) -> ConsentDecision:
    if action not in {a.value for a in MemoryAction}:
        return ConsentDecision(False, str(action), "unsupported action")
    if not owner_authenticated or not owner_id or not memory_owner_id:
        return ConsentDecision(False, action, "owner authentication required")
    if owner_id != memory_owner_id:
        return ConsentDecision(False, action, "cross-owner access prohibited")
    if action == "delete":
        # Deletion must not depend on an earlier storage/recall consent.
        return ConsentDecision(True, action, "authenticated owner deletion permitted")
    if not explicit_consent:
        return ConsentDecision(False, action, "explicit consent required")
    if consent_expires_at is None:
        return ConsentDecision(False, action, "expiring consent required")
    if consent_expires_at.tzinfo is None or consent_expires_at.utcoffset() is None:
        return ConsentDecision(False, action, "timezone-aware expiry required")
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        return ConsentDecision(False, action, "timezone-aware current time required")
    if current >= consent_expires_at:
        return ConsentDecision(False, action, "consent expired")
    return ConsentDecision(True, action, "authorized by current owner consent")
