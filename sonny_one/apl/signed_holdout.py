"""Ed25519 attestation verification; verification does not establish custody."""
import base64
import binascii
import json
from .external_holdout import verify_external_holdout_attestation


def verify_signed_external_holdout(attestation, *, candidate_sha256,
                                   base_revision, expected_evaluator,
                                   trusted_public_key_pem):
    """Require a trusted externally provisioned Ed25519 key and valid signature.

    The public key must be pinned by the caller independently of the candidate
    and attestation. This verifies origin/integrity, not confidential execution.
    """
    result = verify_external_holdout_attestation(
        attestation, candidate_sha256=candidate_sha256,
        base_revision=base_revision, expected_evaluator=expected_evaluator)
    if not isinstance(trusted_public_key_pem, (str, bytes)) or not trusted_public_key_pem:
        raise ValueError("Trusted public key required")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise RuntimeError("Ed25519 verification dependency unavailable") from exc
    try:
        key_bytes = (trusted_public_key_pem.encode("ascii")
                     if isinstance(trusted_public_key_pem, str)
                     else trusted_public_key_pem)
        key = serialization.load_pem_public_key(key_bytes)
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError("Only Ed25519 evaluator keys supported")
        signature = base64.b64decode(attestation["signature"], validate=True)
        if len(signature) != 64:
            raise ValueError("Invalid Ed25519 signature length")
        payload = {k: v for k, v in attestation.items() if k != "signature"}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        key.verify(signature, canonical)
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise ValueError("Invalid evaluator signature or public key") from exc
    except Exception as exc:
        if type(exc).__name__ == "InvalidSignature":
            raise ValueError("Invalid evaluator signature") from exc
        raise
    return {**result, "signature_verified": True,
            "independent_custody_verified": False,
            "promotion": "FORBIDDEN", "improvement_proven": False}
