import pytest
from sonny_one.voice_provider_boundary import LocalSpeechApproval, LocalSpeechBoundary

class STT:
    def transcribe(self, pcm): return "hello"
class TTS:
    def synthesize(self, text): return b"\x00\x00"

def approval(**overrides):
    data=dict(provider_id="local-test",license_reviewed=True,installation_verified=True,network_disabled=True,owner_approved=True)
    data.update(overrides)
    return LocalSpeechApproval(**data)

def make(**overrides):
    return LocalSpeechBoundary(approval=approval(**overrides),stt=STT(),tts=TTS())

@pytest.mark.parametrize("field",["license_reviewed","installation_verified","network_disabled","owner_approved"])
def test_approval_fail_closed(field):
    with pytest.raises(PermissionError): make(**{field:False})

def test_provider_id_required():
    with pytest.raises(ValueError): make(provider_id=" ")

def test_valid_roundtrip():
    b=make(); assert b.transcribe(b"\x00\x00")=="hello";assert b.synthesize("hi")==b"\x00\x00"

def test_invalid_pcm_rejected_before_stt():
    b=make()
    with pytest.raises(ValueError):b.transcribe(b"\x00")

def test_stt_output_bounded():
    b=make()
    class Huge:
        def transcribe(self,pcm):return "x"*4097
    b._stt=Huge()
    with pytest.raises(ValueError):b.transcribe(b"\x00\x00")

def test_invalid_tts_output_rejected():
    b=make()
    class Bad:
        def synthesize(self,text):return b"\x00"
    b._tts=Bad()
    with pytest.raises(ValueError):b.synthesize("hello")

def test_close_blocks_use():
    b=make();b.close()
    with pytest.raises(RuntimeError):b.transcribe(b"\x00\x00")
    with pytest.raises(RuntimeError):b.synthesize("hello")

def test_missing_adapter_methods_rejected():
    with pytest.raises(TypeError):LocalSpeechBoundary(approval=approval(),stt=object(),tts=TTS())
