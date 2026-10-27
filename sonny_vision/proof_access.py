"""Short-lived, job-scoped approval-preview authorization.

This protects access tokens, not the hosting server. The caller must authenticate
the customer, enforce HTTPS, serve only proof bytes, and manage secret rotation.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import time
from base64 import urlsafe_b64encode, urlsafe_b64decode


def _encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_proof_token(job_id: str, customer_id: str, proof_sha256: str,
                      secret: bytes, now: int, ttl_seconds: int = 900) -> str:
    if len(secret) < 32 or not 1 <= ttl_seconds <= 3600:
        raise ValueError("Invalid signing key or token lifetime")
    if not job_id or not customer_id or len(proof_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in proof_sha256):
        raise ValueError("Invalid token claims")
    payload = json.dumps({"job": job_id, "customer": customer_id,
                          "proof": proof_sha256, "expires": int(now) + ttl_seconds},
                         sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(secret, payload, hashlib.sha256).digest()
    return _encode(payload) + "." + _encode(signature)


def verify_proof_token(token: str, job_id: str, customer_id: str,
                       proof_sha256: str, secret: bytes, now: int) -> bool:
    if len(secret) < 32 or len(token) > 2048:
        return False
    try:
        encoded, signature = token.split(".")
        payload = _decode(encoded)
        actual = _decode(signature)
        expected = hmac.new(secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(actual, expected):
            return False
        claims = json.loads(payload)
        return (type(claims) is dict and claims.get("job") == job_id
                and claims.get("customer") == customer_id
                and claims.get("proof") == proof_sha256
                and type(claims.get("expires")) is int
                and int(now) < claims["expires"])
    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
        return False
