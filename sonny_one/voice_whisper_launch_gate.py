"""Prelaunch integrity gate; intentionally does not execute subprocesses."""
from dataclasses import dataclass
from pathlib import Path
from .voice_windows_engine_manifest import SpeechArtifact, verify_local_artifact
from .voice_whisper_source_check import verify_whisper_upstream_sha1

@dataclass(frozen=True)
class WhisperLaunchSpec:
    executable: Path
    executable_artifact: SpeechArtifact
    model: Path
    model_artifact: SpeechArtifact
    upstream_model_sha1: str

def verify_whisper_launch(spec: WhisperLaunchSpec) -> bool:
    if not isinstance(spec, WhisperLaunchSpec):
        raise TypeError("WhisperLaunchSpec required")
    if spec.executable.is_symlink() or spec.model.is_symlink():
        raise ValueError("engine and model symlinks are forbidden")
    if spec.executable.resolve() == spec.model.resolve():
        raise ValueError("engine and model must be distinct files")
    if not verify_local_artifact(spec.executable_artifact, spec.executable):
        return False
    if not verify_local_artifact(spec.model_artifact, spec.model):
        return False
    # Both digest checks validate bytes at their respective read times. They do
    # not pin the path for a future executor. Execution must independently
    # bind the verified artifact bytes in its sandbox before launch.
    return verify_whisper_upstream_sha1(spec.model, spec.upstream_model_sha1)
