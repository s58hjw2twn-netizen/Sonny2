from hashlib import sha1, sha256
from pathlib import Path
import pytest
from sonny_one.voice_windows_engine_manifest import SpeechArtifact
from sonny_one.voice_whisper_launch_gate import WhisperLaunchSpec
from sonny_one.voice_whisper_command import prepare_whisper_command

def make_artifact(name, data):
    return SpeechArtifact(name, "test-v1", "test-only", sha256(data).hexdigest(), len(data))

def setup(tmp_path):
    executable, model, audio = (tmp_path / n for n in ("whisper.exe", "model.bin", "sample.wav"))
    executable.write_bytes(b"test executable")
    model.write_bytes(b"test model")
    audio.write_bytes(b"RIFF" + b"\x00"*4 + b"WAVE" + b"\x00"*36)
    spec = WhisperLaunchSpec(executable, make_artifact("engine", b"test executable"),
                             model, make_artifact("model", b"test model"),
                             sha1(b"test model").hexdigest())
    return spec, audio

def test_verified_command_has_fixed_arguments(tmp_path):
    spec, audio = setup(tmp_path)
    result = prepare_whisper_command(spec, audio)
    assert result.argv == (str(spec.executable.resolve()), "-m", str(spec.model.resolve()),
                           "-f", str(audio.resolve()), "-nt")

def test_tampered_engine_rejected(tmp_path):
    spec, audio = setup(tmp_path)
    spec.executable.write_bytes(b"bad engine")
    with pytest.raises(ValueError):
        prepare_whisper_command(spec, audio)

def test_tampered_model_rejected(tmp_path):
    spec, audio = setup(tmp_path)
    spec.model.write_bytes(b"bad model")
    with pytest.raises(ValueError):
        prepare_whisper_command(spec, audio)

def test_non_wav_input_rejected(tmp_path):
    spec, audio = setup(tmp_path)
    audio.write_bytes(b"x"*50)
    with pytest.raises(ValueError):
        prepare_whisper_command(spec, audio)

def test_wav_symlink_rejected(tmp_path):
    spec, audio = setup(tmp_path)
    alias = tmp_path / "alias.wav"
    alias.symlink_to(audio)
    with pytest.raises(ValueError, match="regular WAV"):
        prepare_whisper_command(spec, alias)

def test_short_wav_rejected(tmp_path):
    spec, audio = setup(tmp_path)
    audio.write_bytes(b"RIFF" + b"\\x00" * 4 + b"WAVE")
    with pytest.raises(ValueError, match="at least 44"):
        prepare_whisper_command(spec, audio)
