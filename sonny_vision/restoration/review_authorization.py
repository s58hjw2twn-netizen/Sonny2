"""HMAC-bound review authorization for research repair decisions.

A trusted backend signs decisions; the photo repair worker verifies them.
This proves possession of the shared secret, not human identity by itself.
"""
import hashlib
import hmac
import json
from pathlib import Path


def canonical_payload(decisions):
    if not isinstance(decisions, dict):
        raise ValueError("decision record must be a JSON object")
    payload = {k:v for k,v in decisions.items() if k != "authorization_hmac_sha256"}
    return json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sign_review(decisions, secret):
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ValueError("at least 32 secret bytes required")
    return hmac.new(secret, canonical_payload(decisions), hashlib.sha256).hexdigest()


def verify_review(decisions, secret, *, expected_reviewer_id=None):
    if not isinstance(decisions, dict):
        raise ValueError("invalid decision record")
    signature = decisions.get("authorization_hmac_sha256")
    reviewer = decisions.get("reviewer_id")
    if not isinstance(signature,str) or len(signature)!=64:
        raise ValueError("missing review signature")
    if not isinstance(reviewer,str) or not reviewer.strip():
        raise ValueError("missing reviewer ID")
    if expected_reviewer_id is not None and reviewer != expected_reviewer_id:
        raise ValueError("reviewer mismatch")
    if decisions.get("reviewer_confirmed") is not True:
        raise ValueError("reviewer confirmation missing")
    expected = sign_review(decisions,secret)
    if not hmac.compare_digest(signature, expected):
        raise ValueError("review authorization invalid or tampered")
    return True


def verify_review_file(path, secret, *, expected_reviewer_id=None):
    return verify_review(json.loads(Path(path).read_text()), secret, expected_reviewer_id=expected_reviewer_id)
