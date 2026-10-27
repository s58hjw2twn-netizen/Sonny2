"""Pinned external evaluator trust configuration.

A public key supplied by an attestation or candidate is never trusted. The
operator must pin evaluator identity and PEM key in a separate trusted input.
This module does not claim that key custody or holdout isolation is proven.
"""
import hashlib
import re
from .signed_holdout import verify_signed_external_holdout

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def verify_with_pinned_evaluator(attestation, *, candidate_sha256,
                                 base_revision, trusted_evaluator_id,
                                 trusted_public_key_pem,
                                 trusted_public_key_sha256):
    """Reject unpinned keys before verifying the Ed25519 evidence signature."""
    if not isinstance(trusted_evaluator_id, str) or not _ID.fullmatch(trusted_evaluator_id):
        raise ValueError("Trusted evaluator identity must be pinned")
    if not isinstance(trusted_public_key_pem, (str, bytes)) or not trusted_public_key_pem:
        raise ValueError("Trusted evaluator public key required")
    key_bytes = (trusted_public_key_pem.encode("ascii")
                 if isinstance(trusted_public_key_pem, str) else trusted_public_key_pem)
    if not isinstance(trusted_public_key_sha256, str) or not _SHA.fullmatch(trusted_public_key_sha256):
        raise ValueError("Trusted key fingerprint must be pinned")
    if hashlib.sha256(key_bytes).hexdigest() != trusted_public_key_sha256:
        raise ValueError("Evaluator public key differs from trusted pin")
    result = verify_signed_external_holdout(
        attestation, candidate_sha256=candidate_sha256,
        base_revision=base_revision, expected_evaluator=trusted_evaluator_id,
        trusted_public_key_pem=key_bytes)
    return {**result, "evaluator_key_pin_verified": True,
            "independent_custody_verified": False,
            "promotion": "FORBIDDEN", "improvement_proven": False}
