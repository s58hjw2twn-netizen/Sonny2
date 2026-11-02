"""Build a minimal Whisper CLI invocation only after artifact verification.

This module never launches a process. Caller must separately enforce sandboxing,
network restrictions, process limits, and approval before execution.
"""
from dataclasses import dataclass
from pathlib import Path
from .voice_whisper_launch_gate import WhisperLaunchSpec, verify_whisper_launch

@dataclass(frozen=True)
class WhisperCommand:
    argv: tuple[str, ...]

def prepare_whisper_command(spec: WhisperLaunchSpec, audio_wav: Path) -> WhisperCommand:
    if not isinstance(audio_wav, Path) or audio_wav.is_symlink() or not audio_wav.is_file():
        raise ValueError("regular WAV input required")
    if audio_wav.suffix.lower() != ".wav":
        raise ValueError("WAV input required")
    if audio_wav.stat().st_size < 44:
        raise ValueError("WAV input too short")
    with audio_wav.open("rb") as stream:
        header = stream.read(12)
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
