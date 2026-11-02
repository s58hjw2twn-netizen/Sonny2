from hashlib import sha256
import pytest
from sonny_one.voice_engine_probe import run_speech_probe
from sonny_one.voice_provider_boundary import LocalSpeechApproval, LocalSpeechBoundary

class STT:
    def transcribe(self, pcm): return "test transcript"
class TTS:
    def synthesize(self, text): return b"\x00\x00"

def boundary():
    approval=LocalSpeechApproval("deterministic-fixture",True,True,True,True)
    return LocalSpeechBoundary(approval=approval,stt=STT(),tts=TTS())

def test_probe_records_hashes_and_bytes():
    pcm=b"\x01\x00"
    result=run_speech_probe(boundary(),provider_id="deterministic-fixture",pcm=pcm,synthesis_text="hello")
    assert result.input_sha256==sha256(pcm).hexdigest()
    assert result.output_sha256==sha256(b"\x00\x00").hexdigest()
    assert result.output_bytes==2
    assert result.transcript=="test transcript"
    assert result.elapsed_ms>=0

@pytest.mark.parametrize("pcm",[b"",b"\x00",b"x"*96001])
def test_invalid_audio_rejected(pcm):
    with pytest.raises(ValueError):
        run_speech_probe(boundary(),provider_id="fixture",pcm=pcm,synthesis_text="hello")

def test_unapproved_boundary_rejected():
    with pytest.raises(TypeError):
        run_speech_probe(object(),provider_id="fixture",pcm=b"\x00\x00",synthesis_text="hello")

def test_missing_provider_id_rejected():
    with pytest.raises(ValueError):
        run_speech_probe(boundary(),provider_id=" ",pcm=b"\x00\x00",synthesis_text="hello")
