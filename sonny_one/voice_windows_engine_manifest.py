"""Pure manifest verification for explicitly approved Windows speech artifacts.

No downloads, process execution, network access, or model installation.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import stat
import re

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")

@dataclass(frozen=True)
class SpeechArtifact:
    name: str
    version: str
    license_id: str
    sha256_hex: str
    size_bytes: int

    def validate(self):
        for field in (self.name, self.version, self.license_id):
            if not isinstance(field, str) or not field.strip():
                raise ValueError("artifact identity and license required")
        if not isinstance(self.sha256_hex, str) or not _SHA256.fullmatch(self.sha256_hex):
            raise ValueError("lowercase SHA256 required")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int) or self.size_bytes <= 0:
            raise ValueError("positive artifact size required")

def verify_local_artifact(artifact: SpeechArtifact, path: Path) -> bool:
    if not isinstance(artifact, SpeechArtifact):
        raise TypeError("SpeechArtifact required")
    artifact.validate()
    if not isinstance(path, Path):
        raise TypeError("Path required")
    # Open with NOFOLLOW so swapping the path to a symlink cannot redirect
    # hashing after the initial path check. Hash the same opened descriptor.
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if not hasattr(os, "O_NOFOLLOW"):
        if path.is_symlink():
            raise ValueError("symlink artifact rejected")
    else:
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ValueError("regular non-symlink file required") from exc
    # fstat before wrapping: fdopen on Linux rejects directory descriptors.
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("regular non-symlink file required")
    except BaseException:
        os.close(fd)
        raise
    with os.fdopen(fd, "rb") as handle:
        if metadata.st_size != artifact.size_bytes:
            return False
        digest = sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
        return digest.hexdigest() == artifact.sha256_hex
