"""Independent-custodian evidence envelope for APL-001.

The custodian key must remain outside the candidate runner. This provides
integrity/authenticity only relative to the key holder, not scientific truth.
"""
import hashlib
import hmac
import json


def _canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def seal_evidence(record, key, *, custodian_id):
    if not isinstance(record, dict) or not record:
        raise ValueError("Nonempty evidence record required")
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("Independent secret key must be at least 32 bytes")
    if not isinstance(custodian_id, str) or not custodian_id.strip():
        raise ValueError("Custodian ID required")
    payload = _canonical(record)
    if len(payload) > 1_000_000:
        raise ValueError("Evidence exceeds size budget")
    digest = hashlib.sha256(payload).hexdigest()
    metadata = {"format": "apl-evidence-envelope-v1", "custodian_id": custodian_id,
                "payload_sha256": digest}
    mac = hmac.new(key, _canonical(metadata), hashlib.sha256).hexdigest()
    return {**metadata, "mac_sha256": mac}


def verify_evidence(record, envelope, key, *, expected_custodian):
    try:
        if not isinstance(record, dict) or not isinstance(envelope, dict):
            return False
        if not isinstance(key, bytes) or len(key) < 32:
            return False
        if not isinstance(expected_custodian, str) or not expected_custodian.strip():
            return False
        if set(envelope) != {"format", "custodian_id", "payload_sha256", "mac_sha256"}:
            return False
        if envelope["format"] != "apl-evidence-envelope-v1":
            return False
        if envelope["custodian_id"] != expected_custodian:
            return False
        payload = _canonical(record)
        if len(payload) > 1_000_000:
            return False
        digest = hashlib.sha256(payload).hexdigest()
        metadata = {k: envelope[k] for k in ("format", "custodian_id", "payload_sha256")}
        mac = hmac.new(key, _canonical(metadata), hashlib.sha256).hexdigest()
        return (isinstance(envelope["payload_sha256"], str)
                and isinstance(envelope["mac_sha256"], str)
                and hmac.compare_digest(digest, envelope["payload_sha256"])
                and hmac.compare_digest(mac, envelope["mac_sha256"]))
    except (TypeError, ValueError, OverflowError):
        return False
