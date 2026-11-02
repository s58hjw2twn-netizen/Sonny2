import pytest
from sonny_one.voice_adapter import VoiceSession, VoiceState


class FakeSpeech:
    def __init__(self):
        self.events = []
    def start(self):
        self.events.append("start")
    def stop(self):
        self.events.append("stop")
    def cancel_output(self):
        self.events.append("cancel")


def test_authentication_required():
    with pytest.raises(PermissionError):
        VoiceSession(FakeSpeech())


def test_interruption_cancels_output():
    fake = FakeSpeech()
    session = VoiceSession(fake, authenticated=True)
    assert session.start().state is VoiceState.LISTENING
    assert session.begin_output().state is VoiceState.SPEAKING
    assert session.interrupt().state is VoiceState.INTERRUPTED
    assert fake.events == ["start", "cancel"]
    assert session.resume_listening().state is VoiceState.LISTENING
    assert session.close().state is VoiceState.IDLE


def test_invalid_transition_rejected():
    session = VoiceSession(FakeSpeech(), authenticated=True)
    with pytest.raises(RuntimeError):
        session.interrupt()


def test_cancel_failure_does_not_claim_interruption():
    class Broken(FakeSpeech):
        def cancel_output(self):
            raise RuntimeError("device failure")
    session = VoiceSession(Broken(), authenticated=True)
    session.start()
    session.begin_output()
    with pytest.raises(RuntimeError):
        session.interrupt()
    assert session.state is VoiceState.SPEAKING
