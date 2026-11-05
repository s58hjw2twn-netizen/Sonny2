import pytest
from sonny.voice_turn import VoiceTurn, ActionStatus, verified_spoken_status


def test_streaming_and_buffer_bounds():
    t = VoiceTurn("user-session", max_audio_bytes=4)
    t.ingest("user-session", 0, b"ab")
    t.ingest("user-session", 1, b"cd")
    with pytest.raises(BufferError):
        t.ingest("user-session", 2, b"x")
    assert t.consume_audio() == b"abcd"
    assert t.consume_audio() == b""


def test_cross_session_and_sequence_rejected():
    t = VoiceTurn("owner")
    with pytest.raises(PermissionError):
        t.ingest("other", 0, b"audio")
    with pytest.raises(ValueError):
        t.ingest("owner", 1, b"audio")


def test_barge_in_invalidates_old_generation():
    t = VoiceTurn("owner")
    old = t.generation
    t.ingest("owner", 0, b"private")
    assert t.allow_output("owner", old)
    t.interrupt()
    assert not t.allow_output("owner", old)
    with pytest.raises(RuntimeError):
        t.consume_audio()
    new = t.start_next_turn()
    assert new != old
    assert t.consume_audio() == b""
    assert not t.allow_output("other", new)
    assert t.allow_output("owner", new)


def test_never_claim_verification_without_evidence():
    with pytest.raises(ValueError):
        verified_spoken_status(ActionStatus.VERIFIED)
    assert "independently verified" in verified_spoken_status(
        ActionStatus.VERIFIED, "ci-run-123"
    )
    for status in (ActionStatus.PROPOSED, ActionStatus.ATTEMPTED,
                   ActionStatus.COMPLETED, ActionStatus.FAILED, ActionStatus.UNKNOWN):
        assert "independently verified" not in verified_spoken_status(status)


@pytest.mark.parametrize("session_id", ["", "   ", None, 12])
def test_reject_invalid_session_identity(session_id):
    with pytest.raises(ValueError):
        VoiceTurn(session_id)


@pytest.mark.parametrize("limit", [0, -1, True, 2.5, "1024"])
def test_reject_invalid_audio_budget(limit):
    with pytest.raises(ValueError):
        VoiceTurn("owner", max_audio_bytes=limit)


def test_rejected_audio_does_not_advance_sequence_or_buffer():
    t = VoiceTurn("owner", max_audio_bytes=2)
    with pytest.raises(BufferError):
        t.ingest("owner", 0, b"abc")
    assert t.next_audio_sequence == 0
    assert t.consume_audio() == b""
    t.ingest("owner", 0, b"ab")
    assert t.consume_audio() == b"ab"
