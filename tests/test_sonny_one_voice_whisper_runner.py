from unittest.mock import patch
import subprocess
import pytest
from sonny_one.voice_whisper_command import WhisperCommand
from sonny_one.voice_whisper_runner import run_prepared_whisper

COMMAND = WhisperCommand(("engine.exe", "-m", "model.bin", "-f", "audio.wav", "-nt"))

def test_approval_required():
    with patch("sonny_one.voice_whisper_runner.subprocess.run") as run:
        with pytest.raises(PermissionError):
            run_prepared_whisper(COMMAND, isolation_verified=True)
        run.assert_not_called()

def test_isolation_required():
    with patch("sonny_one.voice_whisper_runner.subprocess.run") as run:
        with pytest.raises(PermissionError):
            run_prepared_whisper(COMMAND, approved=True)
        run.assert_not_called()

def test_mocked_execution_uses_no_shell():
    with patch("sonny_one.voice_whisper_runner.subprocess.run",
               return_value=subprocess.CompletedProcess([], 0, b"hello", b"")) as run:
        result = run_prepared_whisper(COMMAND, approved=True, isolation_verified=True)
        assert result.stdout == "hello"
        assert result.returncode == 0
        assert run.call_args.kwargs["stdin"] == subprocess.DEVNULL
        assert "shell" not in run.call_args.kwargs

def test_timeout_fails():
    with patch("sonny_one.voice_whisper_runner.subprocess.run",
               side_effect=subprocess.TimeoutExpired([], 1)):
        with pytest.raises(TimeoutError):
            run_prepared_whisper(COMMAND, approved=True, isolation_verified=True)

def test_oversized_output_fails():
    with patch("sonny_one.voice_whisper_runner.subprocess.run",
               return_value=subprocess.CompletedProcess([], 0, b"x"*10, b"")):
        with pytest.raises(ValueError):
            run_prepared_whisper(COMMAND, approved=True, isolation_verified=True,
                                 max_output_bytes=5)
