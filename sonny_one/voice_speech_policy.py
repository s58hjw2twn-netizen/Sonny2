"""Bind a validated speech request to trusted policy without executing it.

A policy check is not a consent signature or a substitute for a sandbox.
The trusted orchestrator must authenticate the operator and prevent replay.
"""
from dataclasses import dataclass
from .voice_speech_execution_authorization import (
    SpeechExecutionAuthorization, validate_speech_authorization,
)

@dataclass(frozen=True)
class TrustedSpeechPolicy:
    permitted_image_digest: str
    permitted_engine_sha256: str
    permitted_model_sha256: str
    max_timeout_seconds: int

def match_speech_policy(request: SpeechExecutionAuthorization,
                        policy: TrustedSpeechPolicy) -> bool:
    if not validate_speech_authorization(request):
        return False
    if not isinstance(policy, TrustedSpeechPolicy):
        raise TypeError("TrustedSpeechPolicy required")
    if type(policy.max_timeout_seconds) is not int or not 1 <= policy.max_timeout_seconds <= 120:
        return False
    return (request.image_digest == policy.permitted_image_digest
            and request.engine_sha256 == policy.permitted_engine_sha256
            and request.model_sha256 == policy.permitted_model_sha256
            and request.timeout_seconds <= policy.max_timeout_seconds)
