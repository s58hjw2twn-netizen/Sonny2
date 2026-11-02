from hashlib import sha256
import pytest
from sonny_one.voice_windows_engine_manifest import SpeechArtifact, verify_local_artifact

def artifact(data):
    return SpeechArtifact("stt-model", "test-1", "test-only", sha256(data).hexdigest(), len(data))

def test_matching_local_artifact(tmp_path):
    data = b"model fixture bytes"
    path = tmp_path / "model.bin"
    path.write_bytes(data)
    assert verify_local_artifact(artifact(data), path)

def test_tampering_fails(tmp_path):
    data = b"model fixture bytes"
    path = tmp_path / "model.bin"
    path.write_bytes(b"tampered model byte")
    assert not verify_local_artifact(artifact(data), path)

def test_symlink_rejected(tmp_path):
    path = tmp_path / "model.bin"
    path.write_bytes(b"test")
    link = tmp_path / "alias.bin"
    try:
        link.symlink_to(path)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError):
        verify_local_artifact(artifact(b"test"), link)

@pytest.mark.parametrize("bad", ["", "abc", "F"*64, "g"*64])
def test_invalid_digest_rejected(bad):
    item = SpeechArtifact("stt", "v1", "license", bad, 10)
    with pytest.raises(ValueError):
        item.validate()

def test_invalid_size_rejected():
    with pytest.raises(ValueError):
        SpeechArtifact("stt", "v1", "license", "a"*64, True).validate()

def test_non_regular_directory_rejected(tmp_path):
    with pytest.raises(ValueError, match="regular"):
        verify_local_artifact(artifact(b"x"), tmp_path)

def test_missing_artifact_rejected(tmp_path):
    with pytest.raises(ValueError, match="regular"):
        verify_local_artifact(artifact(b"x"), tmp_path / "missing.bin")
