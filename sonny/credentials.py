"""Password hashing primitives for AUTH-001.

This module does not enable login or alter existing application routes.
Credentials must never be logged or placed in browser storage.
"""
import base64
import hashlib
import hmac
import os

_SCHEME = "scrypt"
_N = 2**15
_R = 8
_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32
_MAX_PASSWORD_BYTES = 1024


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    raw = password.encode("utf-8")
    if not raw or len(raw) > _MAX_PASSWORD_BYTES:
        raise ValueError("Password length is invalid")
    return raw


def hash_password(password: str) -> str:
    """Create a salted, versioned scrypt password verifier."""
    raw = _password_bytes(password)
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.scrypt(
        raw, salt=salt, n=_N, r=_R, p=_P, dklen=_KEY_BYTES,
        maxmem=64 * 1024 * 1024,
    )
    return "$".join((
        _SCHEME, str(_N), str(_R), str(_P),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(derived).decode("ascii"),
    ))


def verify_password(password: str, stored: str) -> bool:
    """Fail closed on malformed verifiers and mismatched passwords."""
    try:
        raw = _password_bytes(password)
        if not isinstance(stored, str):
            return False
        scheme, n, r, p, salt64, digest64 = stored.split("$")
        if (scheme, n, r, p) != (
            _SCHEME, str(_N), str(_R), str(_P)
        ):
            return False
        salt = base64.b64decode(salt64, validate=True)
        expected = base64.b64decode(digest64, validate=True)
        if len(salt) != _SALT_BYTES or len(expected) != _KEY_BYTES:
            return False
        derived = hashlib.scrypt(
            raw, salt=salt, n=_N, r=_R, p=_P, dklen=_KEY_BYTES,
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(derived, expected)
    except (TypeError, ValueError, UnicodeError, OverflowError):
        return False
