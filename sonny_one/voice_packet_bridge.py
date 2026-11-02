"""Session-bound PCM packet transport adapter.

The caller must establish and authenticate a secure channel independently.
No sockets, credentials, microphone, or inference are created here.
"""
from sonny_one.voice_adapter import VoiceSession, VoiceState
from sonny_one.voice_capture_gate import VoiceCaptureGate
from sonny_one.voice_packet import PacketDecoder, encode_packet
from sonny_one.voice_stream import PCMFrame


class VoicePacketBridge:
    def __init__(self, session: VoiceSession, *, authenticated: bool = False):
        if not authenticated:
            raise PermissionError("authenticated channel required")
        if not isinstance(session, VoiceSession):
            raise TypeError("VoiceSession required")
        self.session = session
        self.capture = VoiceCaptureGate(session, authenticated=True)
        self.decoder = PacketDecoder(authenticated=True)
        self._out_sequence = 0
        self._closed = False

    def receive(self, packet: bytes) -> None:
        if self._closed:
            raise RuntimeError("bridge closed")
        # Reject frames outside listening without consuming their sequence.
        if self.session.state is not VoiceState.LISTENING:
            self.capture.discard()
            raise PermissionError("not listening")
        frame = self.decoder.decode(packet)
        self.capture.ingest(frame)

    def next_packet(self) -> bytes | None:
        if self._closed:
            raise RuntimeError("bridge closed")
        frame = self.capture.take()
        if frame is None:
            return None
        packet = encode_packet(self._out_sequence, frame)
        self._out_sequence += 1
        return packet

    def close(self) -> None:
        if self._closed:
            return
        self.capture.close()
        self.decoder.close()
        self._closed = True
