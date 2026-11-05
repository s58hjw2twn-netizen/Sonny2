"""Provider-neutral voice turn coordination. No network, model, or audio I/O.

OpenAI's MIT-licensed Whisper and Agents SDK are optional adapters, not
dependencies of this module. Never infer tool success from spoken text.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    ATTEMPTED = "attempted"
    COMPLETED = "completed"
    VERIFIED = "independently_verified"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class VoiceTurn:
    session_id: str
    generation: int = 0
    next_audio_sequence: int = 0
    interrupted: bool = False
    max_audio_bytes: int = 262144
    _audio: bytearray = field(default_factory=bytearray, repr=False)

    def __post_init__(self):
        if not self.session_id:
            raise ValueError("session_id required")

    def ingest(self, session_id: str, sequence: int, chunk: bytes) -> None:
        if session_id != self.session_id:
            raise PermissionError("session mismatch")
        if self.interrupted:
            raise RuntimeError("turn interrupted")
        if sequence != self.next_audio_sequence:
            raise ValueError("out-of-order audio")
        if not isinstance(chunk, bytes) or not chunk:
            raise ValueError("nonempty audio bytes required")
        if len(self._audio) + len(chunk) > self.max_audio_bytes:
            raise BufferError("audio buffer limit exceeded")
        self._audio.extend(chunk)
        self.next_audio_sequence += 1

    def consume_audio(self) -> bytes:
        if self.interrupted:
            raise RuntimeError("turn interrupted")
        result = bytes(self._audio)
        self._audio.clear()
        return result

    def interrupt(self) -> int:
        self.generation += 1
        self.interrupted = True
        self._audio.clear()
        return self.generation

    def start_next_turn(self) -> int:
        self.generation += 1
        self.interrupted = False
        self.next_audio_sequence = 0
        self._audio.clear()
        return self.generation

    def allow_output(self, session_id: str, generation: int) -> bool:
        return (session_id == self.session_id and
                generation == self.generation and not self.interrupted)


def verified_spoken_status(status: ActionStatus, evidence_reference: Optional[str] = None) -> str:
    """Return conservative wording; only independently verified actions claim verification."""
    status = ActionStatus(status)
    if status == ActionStatus.VERIFIED:
        if not evidence_reference or not evidence_reference.strip():
            raise ValueError("independent verification requires evidence")
        return "The action was independently verified."
    return {
        ActionStatus.PROPOSED: "The action is proposed, not performed.",
        ActionStatus.ATTEMPTED: "The action was attempted, but completion is unconfirmed.",
        ActionStatus.COMPLETED: "The action reported completion, but independent verification is pending.",
        ActionStatus.FAILED: "The action failed.",
        ActionStatus.UNKNOWN: "The action status is unknown.",
    }[status]
