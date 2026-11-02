from sonny_one.voice_speech_execution_authorization import SpeechExecutionAuthorization
from sonny_one.voice_speech_replay_store import reserve_speech_run

def request(run_id="authorized_run_001"):
    return SpeechExecutionAuthorization(
        run_id, "a"*64, "b"*64, "c"*64, "d"*64, 30
    )

def test_first_reservation_succeeds_second_rejected(tmp_path):
    db = tmp_path / "runs.sqlite"
    assert reserve_speech_run(db, request())
    assert not reserve_speech_run(db, request())

def test_replay_rejected_across_connections(tmp_path):
    db = tmp_path / "runs.sqlite"
    assert reserve_speech_run(db, request())
    assert not reserve_speech_run(db, request())
    assert reserve_speech_run(db, request("authorized_run_002"))

def test_invalid_request_does_not_create_store(tmp_path):
    db = tmp_path / "runs.sqlite"
    assert not reserve_speech_run(db, request("../unsafe"))
    assert not db.exists()
