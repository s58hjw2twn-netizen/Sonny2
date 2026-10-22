"""Isolated tests for AUTH-001 password verifier primitives."""
from sonny.credentials import hash_password, verify_password


def test_password_round_trip():
    verifier = hash_password("a long private passphrase")
    assert verify_password("a long private passphrase", verifier)
    assert not verify_password("incorrect", verifier)


def test_unique_salts():
    first = hash_password("same passphrase")
    second = hash_password("same passphrase")
    assert first != second
    assert verify_password("same passphrase", first)
    assert verify_password("same passphrase", second)


def test_malformed_verifiers_fail_closed():
    for invalid in ("", "plaintext", "scrypt$1$8$1$bad$bad", None):
        assert not verify_password("passphrase", invalid)


def test_empty_password_is_rejected():
    try:
        hash_password("")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty password must be rejected")


def test_password_not_in_verifier():
    password = "distinctive-private-password"
    assert password not in hash_password(password)
