"""Provider-independent, fail-closed voice session boundary.

No microphone access, network connection, credential handling, or tool execution.
An external, authenticated transport must validate user identity before use.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


class SpeechProvider(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def cancel_output(self) -> None: ...


@dataclass(frozen=True)
class VoiceEvent:
    state: VoiceState
    event: str


class VoiceSession:
    """Turn control only; no implicit permission to invoke assistant tools."""

    def __init__(self, provider: SpeechProvider, *, authenticated: bool = False):
        if not authenticated:
            raise PermissionError("authenticated session required")
        self.provider = provider
        self.state = VoiceState.IDLE
        self.revision = 0

    def start(self) -> VoiceEvent:
        if self.state is not VoiceState.IDLE:
            raise RuntimeError("session already active")
        self.provider.start()
        self.state = VoiceState.LISTENING
        self.revision += 1
        return VoiceEvent(self.state, "started")

    def begin_output(self) -> VoiceEvent:
        if self.state not in (VoiceState.LISTENING, VoiceState.INTERRUPTED):
            raise RuntimeError("not ready to speak")
        self.state = VoiceState.SPEAKING
        self.revision += 1
        return VoiceEvent(self.state, "output_started")

    def interrupt(self) -> VoiceEvent:
        if self.state is not VoiceState.SPEAKING:
            raise RuntimeError("no output to interrupt")
        # Cancel before acknowledging the interruption.
        self.provider.cancel_output()
        self.state = VoiceState.INTERRUPTED
        self.revision += 1
        return VoiceEvent(self.state, "output_cancelled")

    def resume_listening(self) -> VoiceEvent:
        if self.state not in (VoiceState.INTERRUPTED, VoiceState.SPEAKING):
            raise RuntimeError("cannot resume listening")
        if self.state is VoiceState.SPEAKING:
            self.provider.cancel_output()
        self.state = VoiceState.LISTENING
        return VoiceEvent(self.state, "listening")

    def close(self) -> VoiceEvent:
        self.provider.stop()
        self.state = VoiceState.IDLE
        self.revision += 1
        return VoiceEvent(self.state, "closed")
