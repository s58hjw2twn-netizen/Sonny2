"""Check Whisper upstream SHA-1 separately from local SHA-256 integrity.

This does not download models or treat SHA-1 as a replacement for SHA-256.
"""
from hashlib import sha1
from pathlib import Path
import os
import stat
import re

WHISPER_BASE_EN_UPSTREAM_SHA1 = "137c40403d78fd54d454da0f9bd998f78703390c"
UPSTREAM_MODEL_SOURCE = "https://huggingface.co/ggerganov/whisper.cpp"
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")

def verify_whisper_upstream_sha1(path: Path, expected: str = WHISPER_BASE_EN_UPSTREAM_SHA1) -> bool:
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        raise ValueError("regular non-symlink model file required")
    if not isinstance(expected, str) or not _HEX40.fullmatch(expected):
        raise ValueError("expected upstream SHA-1 must be 40 lowercase hex characters")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ValueError("regular non-symlink model file required") from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("regular non-symlink model file required")
    except BaseException:
        os.close(fd)
        raise
    with os.fdopen(fd, "rb") as stream:
        digest = sha1()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected
