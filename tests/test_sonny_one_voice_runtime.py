import pytest
from sonny_one.voice_integrated_pipeline import IntegratedVoicePipeline
from sonny_one.voice_runtime import VoiceRuntime

class Provider:
    def start(self): pass
    def stop(self): pass
    def cancel_output(self): pass
class STT:
    def transcribe(self, pcm): return "hello"
class LLM:
    def respond(self, transcript): return "hi"
class TTS:
    def synthesize(self, text): return b"\x00\x00"
def build(approved=True):
    p=IntegratedVoicePipeline(Provider(),authenticated=True); p.start()
    return VoiceRuntime(p,transcriber=STT(),responder=LLM(),synthesizer=TTS(),approved=approved)
def test_cycle():
    out=build().process(b"\x00\x00")
    assert (out.transcript,out.response,out.audio)==("hello","hi",b"\x00\x00")
def test_approval():
    with pytest.raises(PermissionError): build(False)
def test_bounds():
    r=build()
    for bad in (b"",b"x"*96001,"not bytes"):
        with pytest.raises(ValueError): r.process(bad)
def test_interrupted_response():
    r=build()
    class Interrupted:
        def respond(self, text): r.pipeline.interrupt(); return "stale"
    r.responder=Interrupted()
    assert r.process(b"\x00\x00") is None
def test_invalid_synthesis():
    r=build()
    class Invalid:
        def synthesize(self,text): return b""
    r.synthesizer=Invalid()
    with pytest.raises(ValueError): r.process(b"\x00\x00")
    assert r.pipeline.turns.state.value=="listening"
def test_interrupted_synthesis():
    r=build()
    class Interrupted:
        def synthesize(self,text): r.pipeline.interrupt(); return b"\x00\x00"
    r.synthesizer=Interrupted()
    assert r.process(b"\x00\x00") is None
def test_model_failure():
    r=build()
    class Broken:
        def respond(self,text): raise RuntimeError("unavailable")
    r.responder=Broken()
    with pytest.raises(RuntimeError): r.process(b"\x00\x00")
    assert r.pipeline.turns.state.value=="listening"
