"""Legacy host runner must never execute untrusted speech engines."""
from unittest.mock import patch
import pytest
from sonny_one.voice_whisper_command import WhisperCommand
from sonny_one.voice_whisper_runner import run_prepared_whisper

COMMAND = WhisperCommand(("engine.exe", "-m", "model.bin", "-f", "audio.wav", "-nt"))

@pytest.mark.parametrize("approved,isolation_verified", [
    (False, False), (True, False), (False, True), (True, True),
    ("yes", True), (True, 1), ([], True), (True, object())
])
def test_host_runner_fails_closed_even_if_caller_claims_isolation(approved, isolation_verified):
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen") as launch:
        with pytest.raises(PermissionError, match="sandbox executor required"):
            run_prepared_whisper(COMMAND, approved=approved,
                                 isolation_verified=isolation_verified)
        launch.assert_not_called()
