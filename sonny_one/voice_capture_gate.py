"""Authenticated voice capture gate.

Coordinates voice session state and bounded PCM ingress. This is a synchronous
local boundary only; it does not open a microphone or execute an AI model.
"""
from sonny_one.voice_adapter import VoiceSession, VoiceState
from sonny_one.voice_stream import AudioBuffer, PCMFrame


class VoiceCaptureGate:
    def __init__(self, session: VoiceSession, *, authenticated: bool = False):
        if not authenticated:
            raise PermissionError("authenticated capture required")
        if not isinstance(session, VoiceSession):
            raise TypeError("VoiceSession required")
        self.session = session
        self.buffer = AudioBuffer(authenticated=True)
        self._closed = False

    def ingest(self, frame: PCMFrame) -> None:
        if self._closed:
            raise RuntimeError("capture gate closed")
        if self.session.state is not VoiceState.LISTENING:
            raise PermissionError("capture only permitted while listening")
        self.buffer.push(frame)

    def take(self) -> PCMFrame | None:
        if self._closed:
            raise RuntimeError("capture gate closed")
        if self.session.state is not VoiceState.LISTENING:
            raise PermissionError("capture only permitted while listening")
        return self.buffer.pop()

    def discard(self) -> None:
        self.buffer.clear()

    def close(self) -> None:
        if self._closed:
            return
        # Do not claim successful shutdown if provider stop fails.
        self.session.close()
        self.buffer.close()
        self._closed = True
