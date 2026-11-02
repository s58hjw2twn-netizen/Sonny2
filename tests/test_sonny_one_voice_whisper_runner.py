"""Legacy host runner must never execute untrusted speech engines."""
import pytest
from sonny_one.voice_whisper_command import WhisperCommand
from sonny_one.voice_whisper_runner import run_prepared_whisper

COMMAND = WhisperCommand(("engine.exe", "-m", "model.bin", "-f", "audio.wav", "-nt"))

@pytest.mark.parametrize("approved,isolation_verified", [
    (False, False), (True, False), (False, True), (True, True),
    ("yes", True), (True, 1), ([], True), (True, object())
])
def test_host_runner_fails_closed_even_if_caller_claims_isolation(approved, isolation_verified):
    with pytest.raises(PermissionError, match="sandbox executor required"):
        run_prepared_whisper(COMMAND, approved=approved,
                             isolation_verified=isolation_verified)

def test_host_runner_never_executes_even_with_malicious_command():
    command = WhisperCommand(("/bin/sh", "-c", "echo unsafe"))
    with pytest.raises(PermissionError, match="sandbox executor required"):
        run_prepared_whisper(command, approved=True, isolation_verified=True)

def test_host_runner_never_executes_even_with_invalid_limits():
    with pytest.raises(PermissionError, match="sandbox executor required"):
        run_prepared_whisper(COMMAND, approved=True, isolation_verified=True,
                             timeout_seconds=-1, max_output_bytes=-1)
