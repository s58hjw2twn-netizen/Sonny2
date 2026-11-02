"""Explicit, opt-in real speech engine probe.

Runs only caller-provided approved adapters. Does not fetch weights, create
network connections, or provision credentials. A green mock test is not a
real-model acceptance result.
"""
from dataclasses import dataclass
from hashlib import sha256
from time import monotonic
from sonny_one.voice_provider_boundary import LocalSpeechBoundary
from sonny_one.voice_pcm_contract import validate_pcm16

@dataclass(frozen=True)
class SpeechProbeResult:
    provider_id: str
    input_sha256: str
    transcript: str
    output_sha256: str
    output_bytes: int
    elapsed_ms: int

def run_speech_probe(boundary: LocalSpeechBoundary, *, provider_id: str, pcm: bytes,
                     synthesis_text: str) -> SpeechProbeResult:
    if not isinstance(boundary, LocalSpeechBoundary):
        raise TypeError("approved local speech boundary required")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider id required")
    validate_pcm16(pcm, max_bytes=96000)
    start = monotonic()
    transcript = boundary.transcribe(pcm)
    audio = boundary.synthesize(synthesis_text)
    elapsed = round((monotonic() - start) * 1000)
    return SpeechProbeResult(
        provider_id=provider_id,
        input_sha256=sha256(pcm).hexdigest(),
        transcript=transcript,
        output_sha256=sha256(audio).hexdigest(),
        output_bytes=len(audio),
        elapsed_ms=elapsed,
    )
