import pytest
from sonny_one.voice_adapter import VoiceSession
from sonny_one.voice_capture_gate import VoiceCaptureGate
from sonny_one.voice_stream import PCMFrame


class FakeProvider:
    def start(self): pass
    def stop(self): pass
    def cancel_output(self): pass


def new_session():
    return VoiceSession(FakeProvider(), authenticated=True)


def test_gate_authentication_and_type():
    with pytest.raises(PermissionError):
        VoiceCaptureGate(new_session())
    with pytest.raises(TypeError):
        VoiceCaptureGate(object(), authenticated=True)


def test_only_listening_accepts_audio():
    session = new_session()
    gate = VoiceCaptureGate(session, authenticated=True)
    frame = PCMFrame(bytes(2))
    with pytest.raises(PermissionError):
        gate.ingest(frame)
    session.start()
    gate.ingest(frame)
    assert gate.take() == frame
    session.begin_output()
    with pytest.raises(PermissionError):
        gate.ingest(frame)
    with pytest.raises(PermissionError):
        gate.take()
    gate.close()


def test_interrupt_resume_and_close():
    session = new_session()
    gate = VoiceCaptureGate(session, authenticated=True)
    frame = PCMFrame(bytes(2))
    session.start()
    session.begin_output()
    session.interrupt()
    with pytest.raises(PermissionError):
        gate.ingest(frame)
    session.resume_listening()
    gate.ingest(frame)
    assert gate.buffer.buffered_bytes == 2
    gate.close()
    assert gate.buffer.buffered_bytes == 0
    gate.close()
    with pytest.raises(RuntimeError):
        gate.ingest(frame)


def test_audio_before_output_transition_is_not_replayed():
    session = new_session()
    gate = VoiceCaptureGate(session, authenticated=True)
    session.start()
    gate.ingest(PCMFrame(bytes(2)))
    session.begin_output()
    with pytest.raises(PermissionError):
        gate.take()
    session.interrupt()
    session.resume_listening()
    assert gate.take() is None
    gate.close()


def test_take_discards_stale_audio_after_state_change():
    session = new_session()
    gate = VoiceCaptureGate(session, authenticated=True)
    session.start()
    gate.ingest(PCMFrame(bytes(2)))
    session.begin_output()
    with pytest.raises(PermissionError):
        gate.take()
    assert gate.buffer.buffered_bytes == 0
    gate.close()


def test_state_transition_discards_audio_before_next_ingest():
    session = new_session()
    gate = VoiceCaptureGate(session, authenticated=True)
    session.start()
    gate.ingest(PCMFrame(bytes(2)))
    session.begin_output()
    session.interrupt()
    session.resume_listening()
    fresh = PCMFrame(bytes(4))
    gate.ingest(fresh)
    assert gate.take() == fresh
    assert gate.take() is None
    gate.close()


def test_rapid_output_cycle_invalidates_buffer_even_when_gate_not_polled():
    session = new_session()
    gate = VoiceCaptureGate(session, authenticated=True)
    session.start()
    old = PCMFrame(bytes(2))
    gate.ingest(old)
    session.begin_output()
    session.interrupt()
    session.resume_listening()
    # The gate never observed the intermediate speaking state.
    assert gate.take() is None
    gate.close()


def test_failed_stop_does_not_report_gate_closed():
    class FailingStop(FakeProvider):
        def stop(self):
            raise RuntimeError("stop failed")
    session = VoiceSession(FailingStop(), authenticated=True)
    gate = VoiceCaptureGate(session, authenticated=True)
    session.start()
    with pytest.raises(RuntimeError, match="stop failed"):
        gate.close()
    assert session.state.value == "listening"
    gate.ingest(PCMFrame(bytes(2)))
    assert gate.take() is not None
