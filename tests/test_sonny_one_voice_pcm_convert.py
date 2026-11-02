import math
import pytest
from sonny_one.voice_pcm_convert import floats_to_pcm16, pcm16_to_floats
from sonny_one.voice_stream import MAX_FRAME_BYTES


def test_silence_and_extremes():
    frame = floats_to_pcm16([-1.0, 0.0, 1.0])
    assert pcm16_to_floats(frame) == [-1.0, 0.0, 32767 / 32768]


def test_clips_out_of_range_samples():
    assert pcm16_to_floats(floats_to_pcm16([-5.0, 5.0])) == [-1.0, 32767 / 32768]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_rejected(bad):
    with pytest.raises(ValueError):
        floats_to_pcm16([bad])


def test_empty_and_oversized_rejected():
    with pytest.raises(ValueError):
        floats_to_pcm16([])
    with pytest.raises(ValueError):
        floats_to_pcm16([0.0] * (MAX_FRAME_BYTES // 2 + 1))


def test_unvalidated_input_rejected():
    with pytest.raises(TypeError):
        pcm16_to_floats(b"\\x00\\x00")


@pytest.mark.parametrize("bad", [True, False, 10 ** 10000, "0.5", None], ids=["true", "false", "huge-integer", "string", "none"])
def test_non_numeric_and_overflowing_samples_rejected(bad):
    with pytest.raises(ValueError):
        floats_to_pcm16([bad])
