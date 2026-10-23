"""APL-001: conservative policy for experimental patch proposals.

Only experimental target files can be changed. This validator is a first
gate; git apply --check and independent review are still mandatory.
"""
import hashlib
import json
import os
from pathlib import Path
import re

ALLOWED_PREFIX = "sonny_one/apl_targets/"
MAX_PATCH_BYTES = 128 * 1024
PATH_RE = re.compile(r"^[A-Za-z0-9_./-]+$")
HEADER_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)$")


def validate_patch(patch: str) -> list[str]:
    if not isinstance(patch, str) or not patch.strip():
        raise ValueError("Empty patch")
    if len(patch.encode("utf-8")) > MAX_PATCH_BYTES:
        raise ValueError("Patch too large")
    forbidden = (
        "GIT binary patch", "Binary files ", "rename from ", "rename to ",
        "copy from ", "copy to ", "new file mode 120000",
        "old mode 120000", "Submodule ",
    )
    paths = []
    for line in patch.splitlines():
        if line.startswith(forbidden):
            raise ValueError("Binary, rename, copy, symlink or submodule changes prohibited")
        if line.startswith("diff --git "):
            match = HEADER_RE.fullmatch(line)
            if not match or match.group(1) != match.group(2):
                raise ValueError("Invalid or renamed diff path")
            path = match.group(1)
            parts = path.split("/")
            if (not PATH_RE.fullmatch(path) or not path.startswith(ALLOWED_PREFIX)
                    or any(part in ("", ".", "..") for part in parts)):
                raise ValueError("Patch touches a non-experimental path")
            paths.append(path)
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Missing or duplicate file diffs")
    return paths


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def append_lineage(ledger: Path, record: dict) -> str:
    """Hash-linked local audit trail. File permissions/backups still required."""
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    if ledger.exists():
        lines = ledger.read_text(encoding="utf-8").splitlines()
        if lines:
            previous = json.loads(lines[-1])["record_hash"]
    entry = {"previous_hash": previous, **record}
    serialized = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    entry["record_hash"] = sha256_bytes(serialized.encode("utf-8"))
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry["record_hash"]


def verify_lineage(ledger: Path) -> bool:
    previous = "0" * 64
    for line in Path(ledger).read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        recorded = entry.pop("record_hash")
        if entry["previous_hash"] != previous:
            return False
        serialized = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        if sha256_bytes(serialized.encode("utf-8")) != recorded:
            return False
        previous = recorded
    return True
