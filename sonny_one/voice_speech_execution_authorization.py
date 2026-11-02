"""Strict per-run speech authorization record; validation only, never execution.

An authorization record is not proof of user consent or sandbox isolation.
A trusted host must authenticate the issuer and bind the record to a real run.
"""
from dataclasses import dataclass
import re

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_RUN_ID = re.compile(r"[A-Za-z0-9_-]{12,128}\Z")

@dataclass(frozen=True)
class SpeechExecutionAuthorization:
    run_id: str
    engine_sha256: str
    model_sha256: str
    audio_sha256: str
    image_digest: str
    timeout_seconds: int

def validate_speech_authorization(record: SpeechExecutionAuthorization) -> bool:
    if not isinstance(record, SpeechExecutionAuthorization):
        raise TypeError("SpeechExecutionAuthorization required")
    if not isinstance(record.run_id, str) or not _RUN_ID.fullmatch(record.run_id):
        return False
    if not all(isinstance(value, str) and _HEX64.fullmatch(value)
               for value in (record.engine_sha256, record.model_sha256,
                             record.audio_sha256, record.image_digest)):
        return False
    if type(record.timeout_seconds) is not int or not 1 <= record.timeout_seconds <= 120:
        return False
    return True
