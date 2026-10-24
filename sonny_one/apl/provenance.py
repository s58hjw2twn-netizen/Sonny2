"""Local integrity verification for APL experiment reports.

Hash-linked records detect ordinary local tampering, not malicious rewrites.
"""
import json
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
