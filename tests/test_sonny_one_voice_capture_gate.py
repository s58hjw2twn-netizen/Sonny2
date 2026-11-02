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
    frame = PCMFrame(b"\\x00\\x00")
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
