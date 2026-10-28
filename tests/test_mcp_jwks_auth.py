from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from sonny.mcp_jwks_auth import JwksAuthConfig, TokenRejected, verify_jwks_resource_token


ISSUER = "https://issuer.example"
AUDIENCE = "https://sonny.example/mcp"
JWKS = "https://issuer.example/.well-known/jwks.json"


def test_config_rejects_non_https_jwks():
    with pytest.raises(ValueError):
        JwksAuthConfig(ISSUER, AUDIENCE, "http://issuer.example/keys")


def test_verifier_uses_configured_signing_key_and_checks_claims(monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    token = jwt.encode({
        "iss": ISSUER, "aud": AUDIENCE, "sub": "pilot",
        "iat": now, "exp": now + timedelta(minutes=5),
        "scope": "sonny.status.read",
    }, private, algorithm="RS256", headers={"kid": "trusted-key-1"})

    class Key:
        key = private.public_key()

    class FakeJwksClient:
        def __init__(self, uri, timeout, cache_keys):
            assert uri == JWKS
            assert timeout == 5
            assert cache_keys is True

        def get_signing_key_from_jwt(self, presented):
            assert presented == token
            return Key()

    monkeypatch.setattr("jwt.PyJWKClient", FakeJwksClient)
    config = JwksAuthConfig(ISSUER, AUDIENCE, JWKS)
    assert verify_jwks_resource_token(token, config)["sub"] == "pilot"


def test_verifier_rejects_untrusted_or_malformed_token(monkeypatch):
    class FakeJwksClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_signing_key_from_jwt(self, token):
            raise RuntimeError("provider details must not escape")

    monkeypatch.setattr("jwt.PyJWKClient", FakeJwksClient)
    config = JwksAuthConfig(ISSUER, AUDIENCE, JWKS)
    with pytest.raises(TokenRejected, match="Invalid bearer token"):
        verify_jwks_resource_token("not-a-token", config)


@pytest.mark.parametrize("claim_update", [
    {"iss": "https://attacker.example"},
    {"aud": "https://other.example/mcp"},
    {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
    {"scope": "sonny.admin"},
])
def test_verifier_rejects_invalid_claims(claim_update, monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER, "aud": AUDIENCE, "sub": "pilot",
        "iat": now, "exp": now + timedelta(minutes=5),
        "scope": "sonny.status.read",
    }
    claims.update(claim_update)
    token = jwt.encode(claims, private, algorithm="RS256", headers={"kid": "trusted-key-1"})

    class Key:
        key = private.public_key()

    class FakeJwksClient:
        def __init__(self, uri, timeout, cache_keys):
            pass

        def get_signing_key_from_jwt(self, presented):
            return Key()

    monkeypatch.setattr("jwt.PyJWKClient", FakeJwksClient)
    with pytest.raises(TokenRejected):
        verify_jwks_resource_token(token, JwksAuthConfig(ISSUER, AUDIENCE, JWKS))


def test_verifier_rejects_wrong_signing_key(monkeypatch):
    trusted = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    attacker = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    token = jwt.encode({
        "iss": ISSUER, "aud": AUDIENCE, "sub": "pilot",
        "iat": now, "exp": now + timedelta(minutes=5),
        "scope": "sonny.status.read",
    }, attacker, algorithm="RS256", headers={"kid": "attacker-key"})

    class Key:
        key = trusted.public_key()

    class FakeJwksClient:
        def __init__(self, uri, timeout, cache_keys):
            pass

        def get_signing_key_from_jwt(self, presented):
            return Key()

    monkeypatch.setattr("jwt.PyJWKClient", FakeJwksClient)
    with pytest.raises(TokenRejected, match="Invalid bearer token"):
        verify_jwks_resource_token(token, JwksAuthConfig(ISSUER, AUDIENCE, JWKS))


@pytest.mark.parametrize("header", [
    {"alg": "HS256", "kid": "key-a"},
    {"alg": "RS256"},
    {"alg": "RS256", "kid": ""},
    {"alg": "RS256", "kid": "x" * 129},
])
def test_rejects_bad_jwt_header_without_network_lookup(monkeypatch, header):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER, "aud": AUDIENCE, "sub": "pilot",
        "iat": now, "exp": now + timedelta(minutes=5),
        "scope": "sonny.status.read",
    }
    if header["alg"] == "HS256":
        token = jwt.encode(claims, "test-secret-only", algorithm="HS256",
                           headers={"kid": header["kid"]})
    else:
        token = jwt.encode(claims, private, algorithm="RS256",
                           headers={k: v for k, v in header.items() if k != "alg"})

    class FailIfCalled:
        def __init__(self, *args, **kwargs):
            raise AssertionError("JWKS network client must not be constructed")

    monkeypatch.setattr("jwt.PyJWKClient", FailIfCalled)
    with pytest.raises(TokenRejected, match="Invalid bearer token"):
        verify_jwks_resource_token(token, JwksAuthConfig(ISSUER, AUDIENCE, JWKS))
