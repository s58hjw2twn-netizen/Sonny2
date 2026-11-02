import io
import subprocess
from unittest.mock import Mock, patch
import pytest
from sonny_one.voice_whisper_command import WhisperCommand
from sonny_one.voice_whisper_runner import run_prepared_whisper

COMMAND = WhisperCommand(("engine.exe", "-m", "model.bin", "-f", "audio.wav", "-nt"))

def fake_process(stdout=b"hello", stderr=b"", returncode=0, wait_error=None):
    process = Mock()
    process.stdout = io.BytesIO(stdout)
    process.stderr = io.BytesIO(stderr)
    process.returncode = returncode
    if wait_error:
        process.wait.side_effect = [wait_error, returncode]
    else:
        process.wait.return_value = returncode
    return process

def test_approval_required():
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen") as launch:
        with pytest.raises(PermissionError):
            run_prepared_whisper(COMMAND, isolation_verified=True)
        launch.assert_not_called()

def test_isolation_required():
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen") as launch:
        with pytest.raises(PermissionError):
            run_prepared_whisper(COMMAND, approved=True)
        launch.assert_not_called()

def test_mocked_execution_uses_no_shell():
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen",
               return_value=fake_process()) as launch:
        result = run_prepared_whisper(COMMAND, approved=True, isolation_verified=True)
        assert result.stdout == "hello"
        assert result.returncode == 0
        assert launch.call_args.kwargs["shell"] is False
        assert launch.call_args.kwargs["stdin"] == subprocess.DEVNULL

def test_timeout_kills_process():
    process = fake_process(wait_error=subprocess.TimeoutExpired([], 1))
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen", return_value=process):
        with pytest.raises(TimeoutError):
            run_prepared_whisper(COMMAND, approved=True, isolation_verified=True)
    process.kill.assert_called()

def test_oversized_output_kills_process():
    process = fake_process(stdout=b"x"*100)
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen", return_value=process):
        with pytest.raises(ValueError):
            run_prepared_whisper(COMMAND, approved=True, isolation_verified=True,
                                 max_output_bytes=5)
    process.kill.assert_called()

@pytest.mark.parametrize("approved,isolation_verified", [
    ("yes", True), (True, 1), ([], True), (True, object())
])
def test_truthy_nonboolean_authorization_rejected(approved, isolation_verified):
    with patch("sonny_one.voice_whisper_runner.subprocess.Popen") as launch:
        with pytest.raises(TypeError):
            run_prepared_whisper(COMMAND, approved=approved,
                                 isolation_verified=isolation_verified)
        launch.assert_not_called()
