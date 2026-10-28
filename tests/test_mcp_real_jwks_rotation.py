"""Exercise real PyJWT JWKS parsing/selection without network access."""
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from sonny.mcp_jwks_auth import JwksAuthConfig, TokenRejected, verify_jwks_resource_token


ISSUER = "https://issuer.example"
AUDIENCE = "https://sonny.example/mcp"
JWKS_URI = "https://issuer.example/.well-known/jwks.json"


def _token(private, kid, **changes):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER, "aud": AUDIENCE, "sub": "pilot-user",
        "iat": now, "exp": now + timedelta(minutes=5),
        "scope": "sonny.status.read",
    }
    claims.update(changes)
    return jwt.encode(claims, private, algorithm="RS256", headers={"kid": kid})


def _jwk(private, kid):
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key()))
    return {**jwk, "kid": kid, "alg": "RS256", "use": "sig"}


def test_real_jwks_parser_accepts_rotation_and_rejects_missing_key(monkeypatch):
    key_a = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_b = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    active = {"keys": [_jwk(key_a, "key-a")]}
    requested = []

    def read_trusted_jwks(self):
        assert self.uri == JWKS_URI
        requested.append(self.uri)
        return active

    # Only transport is mocked; PyJWT performs real JWK parsing, kid selection
    # and RS256 signature validation. No real provider or network involved.
    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", read_trusted_jwks)
    config = JwksAuthConfig(ISSUER, AUDIENCE, JWKS_URI)

    assert verify_jwks_resource_token(_token(key_a, "key-a"), config)["sub"] == "pilot-user"

    active = {"keys": [_jwk(key_b, "key-b")]}
    assert verify_jwks_resource_token(_token(key_b, "key-b"), config)["sub"] == "pilot-user"
    with pytest.raises(TokenRejected):
        verify_jwks_resource_token(_token(key_a, "key-a"), config)

    assert len(requested) >= 2


def test_real_jwks_parser_rejects_wrong_signature_and_scope(monkeypatch):
    trusted = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    attacker = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    active = {"keys": [_jwk(trusted, "trusted")]}

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", lambda self: active)
    config = JwksAuthConfig(ISSUER, AUDIENCE, JWKS_URI)

    with pytest.raises(TokenRejected):
        verify_jwks_resource_token(_token(attacker, "trusted"), config)
    with pytest.raises(TokenRejected):
        verify_jwks_resource_token(_token(trusted, "trusted", scope="sonny.other"), config)
