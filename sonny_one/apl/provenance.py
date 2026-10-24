"""Local integrity verification for APL experiment reports.

Hash-linked records detect ordinary local tampering, not malicious rewrites.
"""
import json
import hashlib
import hmac
from pathlib import Path
from .policy import sha256_bytes, verify_lineage


def verify_report_lineage(report, ledger):
    if not isinstance(report, dict) or not isinstance(report.get("lineage_hash"), str):
        return False
    path = Path(ledger)
    if not path.is_file() or not verify_lineage(path):
        return False
    payload = dict(report)
    claimed_hash = payload.pop("lineage_hash")
    digest = sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except (ValueError, TypeError):
            return False
        if entry.get("record_hash") != claimed_hash:
            continue
        return (entry.get("report_sha256") == digest
                and entry.get("candidate_id") == payload.get("candidate_id")
                and entry.get("base_revision") == payload.get("base_revision")
                and entry.get("image") == payload.get("image")
                and entry.get("trusted_suite_sha256") == payload.get("trusted_suite_sha256")
                and entry.get("heldout_suite_sha256") == payload.get("heldout_suite_sha256")
                and entry.get("status") == payload.get("status"))
    return False

def create_authenticated_anchor(ledger, key, *, key_id):
    """HMAC local ledger snapshot; only independently held keys provide custody."""
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("A separate secret key of at least 32 bytes is required")
    if not isinstance(key_id, str) or not key_id.strip():
        raise ValueError("Nonempty key identifier required")
    path = Path(ledger)
    if not path.is_file() or not verify_lineage(path):
        raise ValueError("Cannot anchor invalid lineage")
    data = path.read_bytes()
    return {"format": "apl-hmac-anchor-v1", "key_id": key_id,
            "ledger_sha256": hashlib.sha256(data).hexdigest(),
            "mac_sha256": hmac.new(key, data, hashlib.sha256).hexdigest(),
            "note": "Keep key and anchor away from the experimental host"}


def verify_authenticated_anchor(ledger, anchor, key):
    """Fail closed against altered ledger, forged digest, and unknown formats."""
    try:
        if not isinstance(key, bytes) or len(key) < 32 or not isinstance(anchor, dict):
            return False
        if set(anchor) != {"format", "key_id", "ledger_sha256", "mac_sha256", "note"}:
            return False
        if anchor["format"] != "apl-hmac-anchor-v1" or not isinstance(anchor["key_id"], str) or not anchor["key_id"]:
            return False
        path = Path(ledger)
        if not path.is_file() or not verify_lineage(path):
            return False
        data = path.read_bytes()
        return (hmac.compare_digest(hashlib.sha256(data).hexdigest(), anchor["ledger_sha256"])
                and hmac.compare_digest(hmac.new(key, data, hashlib.sha256).hexdigest(), anchor["mac_sha256"]))
    except (OSError, ValueError, TypeError):
        return False
