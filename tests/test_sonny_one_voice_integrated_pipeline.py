import pytest
from sonny_one.voice_integrated_pipeline import IntegratedVoicePipeline
from sonny_one.voice_adapter import VoiceState
from sonny_one.voice_turn_coordinator import TurnState

class Provider:
    def __init__(self): self.events=[]; self.fail=False
    def start(self): self.events.append("start")
    def stop(self): self.events.append("stop")
    def cancel_output(self):
        if self.fail: raise RuntimeError("cancel failed")
        self.events.append("cancel")

def setup():
    p=Provider(); v=IntegratedVoicePipeline(p,authenticated=True); v.start(); return v,p

def test_auth():
    with pytest.raises(PermissionError): IntegratedVoicePipeline(Provider())
def test_complete_cycle():
    v,p=setup(); t=v.submit("hello"); assert v.deliver(t,"hi"); assert v.output_finished(t)
    assert v.turns.state is TurnState.LISTENING
def test_thinking_interrupt():
    v,p=setup(); t=v.submit("hello"); v.interrupt(); assert not v.deliver(t,"old")
def test_speaking_interrupt():
    v,p=setup(); t=v.submit("hello"); v.deliver(t,"hi"); v.interrupt()
    assert p.events==["start","cancel"] and not v.output_finished(t)
def test_failed_cancel():
    v,p=setup(); t=v.submit("hello"); v.deliver(t,"hi"); p.fail=True
    with pytest.raises(RuntimeError): v.interrupt()
    assert v.turns.state is TurnState.SPEAKING and v.session.state is VoiceState.SPEAKING
def test_close_and_replay():
    v,p=setup(); t=v.submit("hello"); v.close()
    with pytest.raises(RuntimeError): v.deliver(t,"stale")
def test_bad_transcript():
    v,p=setup()
    with pytest.raises(ValueError): v.submit(" ")
def test_bad_response():
    v,p=setup(); t=v.submit("hi")
    with pytest.raises(ValueError): v.deliver(t,"x"*8193)
    assert v.session.state is VoiceState.LISTENING
def test_old_ticket():
    v,p=setup(); t=v.submit("hi"); v.interrupt(); new=v.submit("new")
    assert not v.deliver(t,"old") and v.deliver(new,"new")
def test_close_speaking():
    v,p=setup(); t=v.submit("hi"); v.deliver(t,"yes"); v.close()
    assert p.events==["start","cancel","stop"]
def test_close_cancel_failure():
    v,p=setup(); t=v.submit("hi"); v.deliver(t,"yes"); p.fail=True
    with pytest.raises(RuntimeError): v.close()
    assert v.turns.state is TurnState.SPEAKING and "stop" not in p.events
