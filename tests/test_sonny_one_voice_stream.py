import pytest

from sonny_one.voice_stream import (
    AudioBuffer, PCMFrame, MAX_FRAME_BYTES, MAX_BUFFER_BYTES,
)


def test_authentication_required():
    with pytest.raises(PermissionError):
        AudioBuffer()


@pytest.mark.parametrize("payload", [b"", b"\x00", b"\x00" * (MAX_FRAME_BYTES + 2)])
def test_invalid_frame_sizes(payload):
    with pytest.raises(ValueError):
        PCMFrame(payload)


def test_format_rejection():
    with pytest.raises(ValueError):
        PCMFrame(b"\x00\x00", sample_rate=16_000)
    with pytest.raises(ValueError):
        PCMFrame(b"\x00\x00", channels=2)


def test_order_and_capacity():
    buf = AudioBuffer(authenticated=True)
    first = PCMFrame(b"\x01\x00")
    second = PCMFrame(b"\x02\x00")
    buf.push(first)
    buf.push(second)
    assert buf.buffered_bytes == 4
    assert buf.pop() == first
    assert buf.pop() == second
    assert buf.pop() is None


def test_overflow_does_not_modify_buffer():
    buf = AudioBuffer(authenticated=True)
    frame = PCMFrame(b"\x00" * MAX_FRAME_BYTES)
    for _ in range(MAX_BUFFER_BYTES // MAX_FRAME_BYTES):
        buf.push(frame)
    with pytest.raises(BufferError):
        buf.push(frame)
    assert buf.buffered_bytes == MAX_BUFFER_BYTES


def test_close_clears_and_rejects_io():
    buf = AudioBuffer(authenticated=True)
    buf.push(PCMFrame(b"\x00\x00"))
    buf.close()
    assert buf.buffered_bytes == 0
    with pytest.raises(RuntimeError):
        buf.pop()
    with pytest.raises(RuntimeError):
        buf.push(PCMFrame(b"\x00\x00"))
