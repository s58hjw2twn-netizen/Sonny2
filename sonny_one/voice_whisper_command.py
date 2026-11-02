"""Build a minimal Whisper CLI invocation only after artifact verification.

This module never launches a process. Caller must separately enforce sandboxing,
network restrictions, process limits, and approval before execution.
"""
from dataclasses import dataclass
from pathlib import Path
import os
import stat
from .voice_whisper_launch_gate import WhisperLaunchSpec, verify_whisper_launch

@dataclass(frozen=True)
class WhisperCommand:
    argv: tuple[str, ...]

def prepare_whisper_command(spec: WhisperLaunchSpec, audio_wav: Path) -> WhisperCommand:
    if not isinstance(audio_wav, Path) or audio_wav.is_symlink() or not audio_wav.is_file():
        raise ValueError("regular WAV input required")
    if audio_wav.suffix.lower() != ".wav":
        raise ValueError("WAV input required")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(audio_wav, flags)
    except OSError as exc:
        raise ValueError("regular WAV input required") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size < 44:
            raise ValueError("regular WAV of at least 44 bytes required")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            header = stream.read(12)
    finally:
        if fd != -1:
            os.close(fd)
    if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        raise ValueError("invalid WAV container")
    if not verify_whisper_launch(spec):
        raise ValueError("unverified Whisper engine or model")
    return WhisperCommand((
        str(spec.executable.resolve()),
        "-m", str(spec.model.resolve()),
        "-f", str(audio_wav.resolve()),
        "-nt",
    ))
