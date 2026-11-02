"""Offline speech orchestration. Injected adapters; no model, network, or device access."""
from dataclasses import dataclass
from typing import Protocol
from sonny_one.voice_integrated_pipeline import IntegratedVoicePipeline
from sonny_one.voice_pcm_contract import validate_pcm16, validate_synthesized_audio

class Transcriber(Protocol):
    def transcribe(self, pcm: bytes) -> str: ...

class Responder(Protocol):
    def respond(self, transcript: str) -> str: ...

class Synthesizer(Protocol):
    def synthesize(self, response: str) -> bytes: ...

@dataclass(frozen=True)
class VoiceResult:
    transcript: str
    response: str
    audio: bytes

class VoiceRuntime:
    def __init__(self, pipeline: IntegratedVoicePipeline, *, transcriber: Transcriber,
                 responder: Responder, synthesizer: Synthesizer, approved=False):
        if not approved:
            raise PermissionError('speech adapters must be explicitly approved')
        if not isinstance(pipeline, IntegratedVoicePipeline):
            raise TypeError('integrated pipeline required')
        self.pipeline = pipeline
        self.transcriber = transcriber
        self.responder = responder
        self.synthesizer = synthesizer

    def process(self, pcm: bytes) -> VoiceResult | None:
        validate_pcm16(pcm, max_bytes=96000)
        transcript = self.transcriber.transcribe(pcm)
        ticket = self.pipeline.submit(transcript)
        try:
            response = self.responder.respond(transcript)
        except BaseException:
            if self.pipeline.turns._active == ticket and self.pipeline.turns.state.value == 'thinking':
                self.pipeline.interrupt()
            raise
        if not self.pipeline.deliver(ticket, response):
            return None
        try:
            audio = self.synthesizer.synthesize(response)
            validate_synthesized_audio(audio)
            if self.pipeline.turns._active != ticket or self.pipeline.turns.state.value != 'speaking':
                return None
            return VoiceResult(transcript, response, audio)
        except BaseException:
            if self.pipeline.turns._active == ticket and self.pipeline.turns.state.value == 'speaking':
                self.pipeline.interrupt()
            raise
