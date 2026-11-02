"""Bounded in-memory PCM streaming boundary for an authenticated voice session.

No microphone access, model inference, network sockets, or privileged tool calls.
Frames must be mono signed 16-bit little-endian PCM at 24 kHz.
"""
from collections import deque
from dataclasses import dataclass

SAMPLE_RATE = 24_000
BYTES_PER_SAMPLE = 2
MAX_FRAME_MS = 100
MAX_BUFFER_MS = 1000
MAX_FRAME_BYTES = SAMPLE_RATE * BYTES_PER_SAMPLE * MAX_FRAME_MS // 1000
MAX_BUFFER_BYTES = SAMPLE_RATE * BYTES_PER_SAMPLE * MAX_BUFFER_MS // 1000


@dataclass(frozen=True)
class PCMFrame:
    payload: bytes
    sample_rate: int = SAMPLE_RATE
    channels: int = 1

    def __post_init__(self):
        if self.sample_rate != SAMPLE_RATE or self.channels != 1:
            raise ValueError("unsupported PCM format")
        if not isinstance(self.payload, bytes):
            raise TypeError("PCM payload must be bytes")
        if not self.payload or len(self.payload) % BYTES_PER_SAMPLE:
            raise ValueError("invalid PCM sample alignment")
        if len(self.payload) > MAX_FRAME_BYTES:
            raise ValueError("PCM frame too large")


class AudioBuffer:
    def __init__(self, *, authenticated: bool = False):
        if not authenticated:
            raise PermissionError("authenticated voice session required")
        self._frames = deque()
        self._size = 0
        self._closed = False

    def push(self, frame: PCMFrame) -> None:
        if self._closed:
            raise RuntimeError("audio buffer closed")
        if not isinstance(frame, PCMFrame):
            raise TypeError("PCMFrame required")
        if self._size + len(frame.payload) > MAX_BUFFER_BYTES:
            raise BufferError("audio buffer capacity exceeded")
        self._frames.append(frame)
        self._size += len(frame.payload)

    def pop(self) -> PCMFrame | None:
        if self._closed:
            raise RuntimeError("audio buffer closed")
        if not self._frames:
            return None
        frame = self._frames.popleft()
        self._size -= len(frame.payload)
        return frame

    def clear(self) -> None:
        self._frames.clear()
        self._size = 0

    def close(self) -> None:
        self.clear()
        self._closed = True

    @property
    def buffered_bytes(self) -> int:
        return self._size
