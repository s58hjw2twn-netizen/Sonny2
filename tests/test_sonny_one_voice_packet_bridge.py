import pytest
from sonny_one.voice_adapter import VoiceSession
from sonny_one.voice_packet import encode_packet
from sonny_one.voice_packet_bridge import VoicePacketBridge
from sonny_one.voice_stream import PCMFrame


class FakeProvider:
    def start(self): pass
    def stop(self): pass
    def cancel_output(self): pass


def test_requires_authentication():
    session = VoiceSession(FakeProvider(), authenticated=True)
    with pytest.raises(PermissionError):
        VoicePacketBridge(session)


def test_round_trip_and_replay_rejection():
    session = VoiceSession(FakeProvider(), authenticated=True)
    bridge = VoicePacketBridge(session, authenticated=True)
    session.start()
    packet = encode_packet(0, PCMFrame(bytes(4)))
    bridge.receive(packet)
    assert bridge.next_packet() == packet
    assert bridge.next_packet() is None
    with pytest.raises(ValueError):
        bridge.receive(packet)
    bridge.close()


def test_rejects_audio_while_speaking_without_consuming_sequence():
    session = VoiceSession(FakeProvider(), authenticated=True)
    bridge = VoicePacketBridge(session, authenticated=True)
    session.start()
    session.begin_output()
    packet = encode_packet(0, PCMFrame(bytes(2)))
    with pytest.raises(PermissionError):
        bridge.receive(packet)
    session.interrupt()
    session.resume_listening()
    bridge.receive(packet)
    assert bridge.next_packet() == packet
    bridge.close()


def test_stale_audio_discarded_on_rapid_state_cycle():
    session = VoiceSession(FakeProvider(), authenticated=True)
    bridge = VoicePacketBridge(session, authenticated=True)
    session.start()
    bridge.receive(encode_packet(0, PCMFrame(bytes(2))))
    session.begin_output()
    session.interrupt()
    session.resume_listening()
    assert bridge.next_packet() is None
    bridge.receive(encode_packet(1, PCMFrame(bytes(4))))
    assert bridge.next_packet() == encode_packet(0, PCMFrame(bytes(4)))
    bridge.close()


def test_close_rejects_more_packets():
    session = VoiceSession(FakeProvider(), authenticated=True)
    bridge = VoicePacketBridge(session, authenticated=True)
    session.start()
    bridge.close()
    with pytest.raises(RuntimeError):
        bridge.receive(encode_packet(0, PCMFrame(bytes(2))))
    with pytest.raises(RuntimeError):
        bridge.next_packet()
