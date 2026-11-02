from sonny_one.voice_speech_execution_authorization import SpeechExecutionAuthorization
from sonny_one.voice_speech_policy import TrustedSpeechPolicy, match_speech_policy

def request(**kwargs):
    fields = dict(run_id="authorized_run_001", engine_sha256="a"*64,
                  model_sha256="b"*64, audio_sha256="c"*64,
                  image_digest="d"*64, timeout_seconds=30)
    fields.update(kwargs)
    return SpeechExecutionAuthorization(**fields)

def policy(**kwargs):
    fields = dict(permitted_image_digest="d"*64,
                  permitted_engine_sha256="a"*64,
                  permitted_model_sha256="b"*64, max_timeout_seconds=30)
    fields.update(kwargs)
    return TrustedSpeechPolicy(**fields)

def test_exact_policy_match_is_only_eligibility_not_consent():
    assert match_speech_policy(request(), policy())

def test_different_image_engine_model_or_timeout_denied():
    assert not match_speech_policy(request(image_digest="e"*64), policy())
    assert not match_speech_policy(request(engine_sha256="e"*64), policy())
    assert not match_speech_policy(request(model_sha256="e"*64), policy())
    assert not match_speech_policy(request(timeout_seconds=31), policy())

def test_malformed_policy_limits_fail_closed():
    for value in (0, 121, True, "30"):
        assert not match_speech_policy(request(), policy(max_timeout_seconds=value))

def test_malformed_request_denied():
    assert not match_speech_policy(request(run_id="../unsafe"), policy())
