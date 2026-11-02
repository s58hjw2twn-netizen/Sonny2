"""Provider-independent Sonny Voice turn coordinator.

No audio I/O, network, model inference, or privileged tool execution.
Designed as an additive module for Sonny2's voice_adapter.py.
"""
from dataclasses import dataclass
from enum import Enum
import secrets

class TurnState(str, Enum):
    IDLE = 'idle'
    LISTENING = 'listening'
    THINKING = 'thinking'
    SPEAKING = 'speaking'
    CLOSED = 'closed'

@dataclass(frozen=True)
class TurnTicket:
    session_id: str
    turn: int

class VoiceTurnCoordinator:
    """Reject stale model responses after barge-in, reset, or close."""
    def __init__(self, *, authenticated: bool = False, cancel_output=None):
        if authenticated is not True:
            raise PermissionError('authenticated voice session required')
        if cancel_output is None or not callable(cancel_output):
            raise ValueError('cancellation callback required')
        self._cancel = cancel_output
        self._id = secrets.token_hex(16)
        self._turn = 0
        self.state = TurnState.IDLE
        self._active = None

    def start(self):
        if self.state is not TurnState.IDLE:
            raise RuntimeError('session already started')
        self.state = TurnState.LISTENING

    def submit_transcript(self, text):
        if self.state is not TurnState.LISTENING:
            raise RuntimeError('not listening')
        if not isinstance(text, str) or not text.strip() or len(text) > 4096:
            raise ValueError('invalid transcript')
        self._turn += 1
        self._active = TurnTicket(self._id, self._turn)
        self.state = TurnState.THINKING
        return self._active

    def accept_response(self, ticket, text):
        if not isinstance(ticket, TurnTicket) or ticket != self._active or self.state is not TurnState.THINKING:
            return False
        if not isinstance(text, str) or not text.strip() or len(text) > 8192:
            raise ValueError('invalid response')
        self.state = TurnState.SPEAKING
        return True

    def interrupt(self):
        if self.state not in (TurnState.THINKING, TurnState.SPEAKING):
            raise RuntimeError('nothing to interrupt')
        if self.state is TurnState.SPEAKING:
            self._cancel()
        self._turn += 1
        self._active = None
        self.state = TurnState.LISTENING

    def output_finished(self, ticket):
        if self.state is not TurnState.SPEAKING or ticket != self._active:
            return False
        self._active = None
        self.state = TurnState.LISTENING
        return True

    def close(self):
        if self.state is TurnState.CLOSED:
            return
        if self.state is TurnState.SPEAKING:
            self._cancel()
        self._turn += 1
        self._active = None
        self.state = TurnState.CLOSED
