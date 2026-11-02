"""Legacy direct-host Whisper execution is disabled until a sandbox-owned executor exists."""
from dataclasses import dataclass
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
    """Fail closed: caller-supplied approval/isolation flags prove nothing."""
    raise PermissionError("direct host Whisper execution disabled; sandbox executor required")
