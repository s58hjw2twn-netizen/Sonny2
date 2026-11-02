from hashlib import sha1, sha256
from pathlib import Path
import pytest
from sonny_one.voice_whisper_launch_gate import WhisperLaunchSpec, verify_whisper_launch
from sonny_one.voice_windows_engine_manifest import SpeechArtifact

def make_artifact(name, data):
    return SpeechArtifact(name, "fixture-v1", "test-only", sha256(data).hexdigest(), len(data))

def make_spec(tmp_path):
    engine_data = b"fake executable"
    model_data = b"fake model"
    engine = tmp_path / "engine.exe"
    model = tmp_path / "model.bin"
    engine.write_bytes(engine_data)
    model.write_bytes(model_data)
    return WhisperLaunchSpec(engine, make_artifact("engine", engine_data), model,
                             make_artifact("model", model_data), sha1(model_data).hexdigest())

def test_verified_fixture_passes(tmp_path):
    assert verify_whisper_launch(make_spec(tmp_path))

def test_engine_tampering_fails(tmp_path):
    spec = make_spec(tmp_path)
    spec.executable.write_bytes(b"tampered")
    assert not verify_whisper_launch(spec)

def test_model_tampering_fails(tmp_path):
    spec = make_spec(tmp_path)
    spec.model.write_bytes(b"tampered")
    assert not verify_whisper_launch(spec)

def test_wrong_upstream_hash_fails(tmp_path):
    spec = make_spec(tmp_path)
    changed = WhisperLaunchSpec(spec.executable, spec.executable_artifact, spec.model,
                                spec.model_artifact, "0" * 40)
    assert not verify_whisper_launch(changed)

def test_same_file_rejected(tmp_path):
    spec = make_spec(tmp_path)
    changed = WhisperLaunchSpec(spec.executable, spec.executable_artifact, spec.executable,
                                spec.model_artifact, spec.upstream_model_sha1)
    with pytest.raises(ValueError):
        verify_whisper_launch(changed)
