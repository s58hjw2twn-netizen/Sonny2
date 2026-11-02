"""Golden compatibility vectors shared with ios/SonnyVoiceCore/VoiceWireTests.swift.

The Swift XCTest vectors and this Python test must agree byte-for-byte.
Neither test opens a microphone, network connection, or model.
"""
import pytest

from sonny_one.voice_pcm_convert import floats_to_pcm16
from sonny_one.voice_packet import PacketDecoder, encode_packet
from sonny_one.voice_stream import PCMFrame


def test_swift_python_pcm16_golden_vector():
    frame = floats_to_pcm16([-1.0, 0.0, 1.0])
    assert frame.payload == bytes.fromhex("00800000ff7f")


def test_swift_python_packet_golden_vector():
    frame = PCMFrame(bytes.fromhex("0080ff7f"))
    packet = encode_packet(0, frame)
    assert packet == bytes.fromhex("535630310000000000000000000000040080ff7f")
    decoder = PacketDecoder(authenticated=True)
    assert decoder.decode(packet) == frame
    with pytest.raises(ValueError):
        decoder.decode(packet)


def test_out_of_order_frame_cannot_advance_decoder():
    decoder = PacketDecoder(authenticated=True)
    with pytest.raises(ValueError):
        decoder.decode(encode_packet(1, PCMFrame(bytes.fromhex("0000"))))
    assert decoder.decode(encode_packet(0, PCMFrame(bytes.fromhex("0000"))))
