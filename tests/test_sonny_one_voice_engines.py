import pytest
from sonny_one.voice_engines import VoiceEngineOption, VoiceEngineRegistry
from sonny_one.voice_adapter import VoiceSession, VoiceState


class Dummy:
    def __init__(self):
        self.events = []
    def start(self):
        self.events.append("start")
    def stop(self):
        self.events.append("stop")
    def cancel_output(self):
        self.events.append("cancel")


def test_unapproved_engine_rejected():
    registry = VoiceEngineRegistry([VoiceEngineOption("moshi", Dummy())])
    with pytest.raises(PermissionError):
        registry.select("moshi")


def test_network_required_engine_rejected():
    option = VoiceEngineOption("remote", Dummy(), True, True, True, True)
    with pytest.raises(PermissionError):
        VoiceEngineRegistry([option]).select("remote")


def test_duplicate_engines_rejected():
    with pytest.raises(ValueError):
        VoiceEngineRegistry([VoiceEngineOption("x", Dummy()), VoiceEngineOption("x", Dummy())])


def test_approved_local_engine_can_run_turn_control():
    engine = Dummy()
    registry = VoiceEngineRegistry([VoiceEngineOption("local", engine, True, True, True)])
    session = VoiceSession(registry.select("local"), authenticated=True)
    session.start()
    session.begin_output()
    session.interrupt()
    session.resume_listening()
    session.close()
    assert engine.events == ["start", "cancel", "stop"]
    assert session.state is VoiceState.IDLE
