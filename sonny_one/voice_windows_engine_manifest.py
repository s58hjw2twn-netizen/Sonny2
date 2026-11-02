"""Pure manifest verification for explicitly approved Windows speech artifacts.

No downloads, process execution, network access, or model installation.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
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
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular non-symlink file required")
    if path.stat().st_size != artifact.size_bytes:
        return False
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == artifact.sha256_hex
