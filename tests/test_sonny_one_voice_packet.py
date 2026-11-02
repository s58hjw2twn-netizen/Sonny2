import pytest
from sonny_one.voice_packet import encode_packet, PacketDecoder, MAX_PACKET_BYTES
from sonny_one.voice_stream import PCMFrame

def test_roundtrip_and_replay():
    d=PacketDecoder(authenticated=True)
    p=encode_packet(0,PCMFrame(bytes(4)))
    assert d.decode(p)==PCMFrame(bytes(4))
    with pytest.raises(ValueError):d.decode(p)
    assert d.decode(encode_packet(1,PCMFrame(bytes(2))))==PCMFrame(bytes(2))

def test_authentication_and_sequence():
    with pytest.raises(PermissionError):PacketDecoder()
    d=PacketDecoder(authenticated=True)
    with pytest.raises(ValueError):d.decode(encode_packet(1,PCMFrame(bytes(2))))
    assert d.decode(encode_packet(0,PCMFrame(bytes(2))))

def test_invalid_packets_do_not_advance_sequence():
    d=PacketDecoder(authenticated=True)
    good=encode_packet(0,PCMFrame(bytes(2)))
    for bad in [good[:-1],b'BAD!'+good[4:],good+b'\\0',b'',bytes(MAX_PACKET_BYTES+1)]:
        with pytest.raises(ValueError):d.decode(bad)
    assert d.decode(good)

def test_invalid_sequence_and_type():
    for seq in [-1,True,1<<64,'0']:
        with pytest.raises(ValueError):encode_packet(seq,PCMFrame(bytes(2)))
    with pytest.raises(TypeError):encode_packet(0,object())
    with pytest.raises(TypeError):PacketDecoder(authenticated=True).decode('bad')

def test_close():
    d=PacketDecoder(authenticated=True)
    d.close()
    with pytest.raises(RuntimeError):d.decode(encode_packet(0,PCMFrame(bytes(2))))
