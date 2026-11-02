"""Bounded subprocess execution; NOT an isolation or sandbox boundary.

Only call after explicit owner approval and separately verified isolation.
"""
from dataclasses import dataclass
import subprocess
from .voice_whisper_command import WhisperCommand

@dataclass(frozen=True)
class WhisperRunResult:
    returncode: int
    stdout: str
    stderr: str

def run_prepared_whisper(command: WhisperCommand, *, approved: bool = False,
                         isolation_verified: bool = False,
                         timeout_seconds: int = 30,
                         max_output_bytes: int = 65536) -> WhisperRunResult:
    if not approved or not isolation_verified:
        raise PermissionError("explicit approval and independent isolation verification required")
    if not isinstance(command, WhisperCommand) or len(command.argv) != 6:
        raise ValueError("expected prepared Whisper command")
    if command.argv[1] != "-m" or command.argv[3] != "-f" or command.argv[5] != "-nt":
        raise ValueError("unexpected Whisper arguments")
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= 120:
        raise ValueError("timeout out of bounds")
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or not 1 <= max_output_bytes <= 65536:
        raise ValueError("output limit out of bounds")
    try:
        completed = subprocess.run(
            list(command.argv), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout_seconds, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Whisper execution timed out") from exc
    if len(completed.stdout) > max_output_bytes or len(completed.stderr) > max_output_bytes:
        raise ValueError("Whisper output exceeded limit")
    return WhisperRunResult(completed.returncode,
                            completed.stdout.decode("utf-8", errors="replace"),
                            completed.stderr.decode("utf-8", errors="replace"))
