"""Strict 24 kHz mono PCM16 contract for voice runtime input and output.

No device, model, network, or external service is invoked.
"""
from sonny_one.voice_stream import SAMPLE_RATE, BYTES_PER_SAMPLE, MAX_FRAME_BYTES

def validate_pcm16(payload: bytes, *, max_bytes: int) -> bytes:
    if not isinstance(payload, bytes):
        raise TypeError("PCM16 payload must be bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < BYTES_PER_SAMPLE:
        raise ValueError("invalid PCM bound")
    if not payload or len(payload) > max_bytes or len(payload) % BYTES_PER_SAMPLE:
        raise ValueError("PCM16 payload invalid or exceeds bound")
    return payload

def validate_capture_frame(payload: bytes) -> bytes:
    return validate_pcm16(payload, max_bytes=MAX_FRAME_BYTES)

def validate_synthesized_audio(payload: bytes) -> bytes:
    return validate_pcm16(payload, max_bytes=960000)
