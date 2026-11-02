"""Strict binary framing for authenticated voice transport boundaries.

Authentication and encryption belong to the enclosing trusted transport.
This module only validates framing, sequence order, and PCM format.
"""
import struct
from sonny_one.voice_stream import PCMFrame, MAX_FRAME_BYTES

_MAGIC = b'SV01'
_HEADER = struct.Struct('!4sQI')
MAX_PACKET_BYTES = _HEADER.size + MAX_FRAME_BYTES


def encode_packet(sequence: int, frame: PCMFrame) -> bytes:
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not 0 <= sequence < (1 << 64):
        raise ValueError('invalid sequence')
    if not isinstance(frame, PCMFrame):
        raise TypeError('validated PCMFrame required')
    return _HEADER.pack(_MAGIC, sequence, len(frame.payload)) + frame.payload


class PacketDecoder:
    """Rejects replayed, reordered, truncated, and malformed packets."""

    def __init__(self, *, authenticated: bool = False):
        if not authenticated:
            raise PermissionError('authenticated transport required')
        self._next_sequence = 0
        self._closed = False

    def decode(self, packet: bytes) -> PCMFrame:
        if self._closed:
            raise RuntimeError('decoder closed')
        if not isinstance(packet, bytes):
            raise TypeError('packet must be bytes')
        if len(packet) < _HEADER.size or len(packet) > MAX_PACKET_BYTES:
            raise ValueError('invalid packet size')
        magic, sequence, length = _HEADER.unpack_from(packet)
        if magic != _MAGIC or length != len(packet) - _HEADER.size:
            raise ValueError('invalid packet header')
        if sequence != self._next_sequence:
            raise ValueError('out-of-order or replayed packet')
        frame = PCMFrame(packet[_HEADER.size:])
        self._next_sequence += 1
        return frame

    def close(self) -> None:
        self._closed = True
