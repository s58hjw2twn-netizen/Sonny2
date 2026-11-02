"""Pure audio sample conversion for the Moshi Swift Float32 boundary.

Little-endian mono Float32 in [-1, 1] to signed PCM16 and back.
No device permissions, network access, or model inference.
"""
import math
import struct

from sonny_one.voice_stream import PCMFrame, MAX_FRAME_BYTES

MAX_SAMPLES = MAX_FRAME_BYTES // 2


def floats_to_pcm16(samples: list[float]) -> PCMFrame:
    if not samples or len(samples) > MAX_SAMPLES:
        raise ValueError("invalid sample count")
    packed = bytearray()
    for sample in samples:
        if isinstance(sample, bool) or not isinstance(sample, (int, float)):
            raise ValueError("invalid audio sample")
        try:
            normalized = float(sample)
        except (OverflowError, ValueError):
            raise ValueError("invalid audio sample") from None
        if not math.isfinite(normalized):
            raise ValueError("invalid audio sample")
        clipped = max(-1.0, min(1.0, normalized))
        quantized = max(-32768, min(32767, round(clipped * 32768)))
        packed.extend(struct.pack("<h", quantized))
    return PCMFrame(bytes(packed))


def pcm16_to_floats(frame: PCMFrame) -> list[float]:
    if not isinstance(frame, PCMFrame):
        raise TypeError("validated PCMFrame required")
    return [value / 32768.0 for (value,) in struct.iter_unpack("<h", frame.payload)]
