import pytest
from sonny_one.voice_pcm_contract import (
    validate_pcm16, validate_capture_frame, validate_synthesized_audio,
)

@pytest.mark.parametrize("payload", [b"", b"\x00", b"\x00"*4801, "not bytes", None])
def test_capture_rejects_invalid(payload):
    with pytest.raises((TypeError, ValueError)):
        validate_capture_frame(payload)

def test_capture_accepts_frame():
    assert validate_capture_frame(b"\x00\x00"*2400) == b"\x00\x00"*2400

@pytest.mark.parametrize("payload", [b"", b"\x00", b"\x00"*960001, None])
def test_synthesis_rejects_invalid(payload):
    with pytest.raises((TypeError, ValueError)):
        validate_synthesized_audio(payload)

def test_synthesis_accepts_aligned():
    assert validate_synthesized_audio(b"\x00\x00"*4800) == b"\x00\x00"*4800

def test_limit_validation():
    with pytest.raises(ValueError):
        validate_pcm16(b"\x00\x00", max_bytes=True)

def test_runtime_rejects_odd_input_before_transcription():
    from sonny_one.voice_runtime import VoiceRuntime
    from sonny_one.voice_integrated_pipeline import IntegratedVoicePipeline
    class P:
        def start(self): pass
        def stop(self): pass
        def cancel_output(self): pass
    class STT:
        def transcribe(self,pcm): raise AssertionError("should not run")
    pipeline=IntegratedVoicePipeline(P(),authenticated=True)
    pipeline.start()
    runtime=VoiceRuntime(pipeline,transcriber=STT(),responder=object(),synthesizer=object(),approved=True)
    with pytest.raises(ValueError):
        runtime.process(b"\x00")
