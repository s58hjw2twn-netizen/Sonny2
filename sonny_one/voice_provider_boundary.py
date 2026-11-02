"""Fail-closed local speech provider boundary.

No process spawning, network, microphone, credential forwarding, or model loading.
The caller must supply audited adapters; this class is not an isolation sandbox.
"""
from dataclasses import dataclass
from sonny_one.voice_pcm_contract import validate_pcm16, validate_synthesized_audio

@dataclass(frozen=True)
class LocalSpeechApproval:
    provider_id: str
    license_reviewed: bool
    installation_verified: bool
    network_disabled: bool
    owner_approved: bool

    def verify(self):
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider id required")
        if not all(v is True for v in (
            self.license_reviewed, self.installation_verified,
            self.network_disabled, self.owner_approved
        )):
            raise PermissionError("local speech provider not approved")

class LocalSpeechBoundary:
    def __init__(self, *, approval: LocalSpeechApproval, stt, tts):
        if not isinstance(approval, LocalSpeechApproval):
            raise TypeError("LocalSpeechApproval required")
        approval.verify()
        if not callable(getattr(stt, "transcribe", None)):
            raise TypeError("STT transcribe method required")
        if not callable(getattr(tts, "synthesize", None)):
            raise TypeError("TTS synthesize method required")
        self._stt = stt
        self._tts = tts
        self._closed = False

    def transcribe(self, pcm: bytes) -> str:
        self._require_open()
        validate_pcm16(pcm, max_bytes=96000)
        text = self._stt.transcribe(pcm)
        if not isinstance(text, str) or not text.strip() or len(text) > 4096:
            raise ValueError("invalid STT transcript")
        return text

    def synthesize(self, text: str) -> bytes:
        self._require_open()
        if not isinstance(text, str) or not text.strip() or len(text) > 8192:
            raise ValueError("invalid synthesis text")
        return validate_synthesized_audio(self._tts.synthesize(text))

    def close(self):
        self._closed = True

    def _require_open(self):
        if self._closed:
            raise RuntimeError("speech provider boundary closed")
