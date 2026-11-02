from sonny_one.voice_speech_execution_authorization import (
    SpeechExecutionAuthorization, validate_speech_authorization,
)

def make_record(**overrides):
    values = dict(run_id="authorized_run_001", engine_sha256="a"*64,
                  model_sha256="b"*64, audio_sha256="c"*64,
                  image_digest="d"*64, timeout_seconds=30)
    values.update(overrides)
    return SpeechExecutionAuthorization(**values)

def test_well_formed_record_is_only_schema_valid():
    assert validate_speech_authorization(make_record())

def test_reject_missing_or_invalid_run_identifier():
    for value in ("", "../unsafe", "short", "a"*129):
        assert not validate_speech_authorization(make_record(run_id=value))

def test_reject_invalid_digests():
    for field in ("engine_sha256", "model_sha256", "audio_sha256", "image_digest"):
        for value in ("", "F"*64, "z"*64):
            assert not validate_speech_authorization(make_record(**{field: value}))

def test_reject_invalid_timeouts():
    for value in (0, 121, -1, True, 1.5, "30"):
        assert not validate_speech_authorization(make_record(timeout_seconds=value))
