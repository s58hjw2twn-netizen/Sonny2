"""Check Whisper upstream SHA-1 separately from local SHA-256 integrity.

This does not download models or treat SHA-1 as a replacement for SHA-256.
"""
from hashlib import sha1
from pathlib import Path
import re

WHISPER_BASE_EN_UPSTREAM_SHA1 = "137c40403d78fd54d454da0f9bd998f78703390c"
UPSTREAM_MODEL_SOURCE = "https://huggingface.co/ggerganov/whisper.cpp"
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")

def verify_whisper_upstream_sha1(path: Path, expected: str = WHISPER_BASE_EN_UPSTREAM_SHA1) -> bool:
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        raise ValueError("regular non-symlink model file required")
    if not isinstance(expected, str) or not _HEX40.fullmatch(expected):
        raise ValueError("expected upstream SHA-1 must be 40 lowercase hex characters")
    digest = sha1()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected
