from hashlib import sha1
import pytest
from sonny_one.voice_whisper_source_check import (
    WHISPER_BASE_EN_UPSTREAM_SHA1,
    verify_whisper_upstream_sha1,
)

def test_official_reference_is_sha1_not_sha256():
    assert len(WHISPER_BASE_EN_UPSTREAM_SHA1) == 40

def test_upstream_hash_matches_local_fixture(tmp_path):
    data = b"fixture model"
    path = tmp_path / "fixture.bin"
    path.write_bytes(data)
    assert verify_whisper_upstream_sha1(path, sha1(data).hexdigest())

def test_changed_bytes_rejected(tmp_path):
    data = b"fixture model"
    path = tmp_path / "fixture.bin"
    path.write_bytes(b"tampered")
    assert not verify_whisper_upstream_sha1(path, sha1(data).hexdigest())

@pytest.mark.parametrize("invalid", ["", "0"*64, "Z"*40])
def test_invalid_hash_fails_closed(tmp_path, invalid):
    path = tmp_path / "fixture.bin"
    path.write_bytes(b"test")
    with pytest.raises(ValueError):
        verify_whisper_upstream_sha1(path, invalid)

def test_upstream_hash_rejects_symlink(tmp_path):
    data = b"fixture model"
    target = tmp_path / "model.bin"
    target.write_bytes(data)
    alias = tmp_path / "alias.bin"
    alias.symlink_to(target)
    with pytest.raises(ValueError, match="non-symlink"):
        verify_whisper_upstream_sha1(alias, sha1(data).hexdigest())

def test_upstream_hash_rejects_directory(tmp_path):
    with pytest.raises(ValueError, match="regular"):
        verify_whisper_upstream_sha1(tmp_path, sha1(b"").hexdigest())
