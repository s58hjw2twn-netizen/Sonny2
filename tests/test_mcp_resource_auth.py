"""Independent unit tests for the isolated resource-token validator."""
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from sonny.mcp_resource_auth import ResourceAuthConfig, TokenRejected, verify_resource_token


@pytest.fixture
def keys():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, public_pem


@pytest.fixture
def config(keys):
    return ResourceAuthConfig("https://issuer.example", "https://sonny.example/mcp", keys[1])


def token(keys, **overrides):
    now = datetime.now(timezone.utc)
    claims = dict(
        iss="https://issuer.example",
        aud="https://sonny.example/mcp",
        sub="pilot-user",
        iat=now,
        exp=now + timedelta(minutes=5),
        scope="sonny.status.read",
    )
    claims.update(overrides)
    return jwt.encode(claims, keys[0], algorithm="RS256")


def test_valid_scoped_token(keys, config):
    assert verify_resource_token(token(keys), config)["sub"] == "pilot-user"


@pytest.mark.parametrize("change", [
    {"iss": "https://wrong.example"},
    {"aud": "https://wrong.example/mcp"},
    {"scope": "sonny.other"},
    {"scope": "sonny.status.read.extra"},
    {"sub": ""},
    {"exp": datetime(2000, 1, 1, tzinfo=timezone.utc)},
])
def test_invalid_claims_rejected(keys, config, change):
    with pytest.raises(TokenRejected):
        verify_resource_token(token(keys, **change), config)


def test_wrong_signing_key_rejected(keys, config):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode({
        "iss": config.issuer, "aud": config.audience, "sub": "pilot-user",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "scope": config.required_scope,
    }, other, algorithm="RS256")
    with pytest.raises(TokenRejected):
        verify_resource_token(forged, config)


def test_unsigned_or_empty_token_rejected(config):
    for value in ("", "not-a-jwt"):
        with pytest.raises(TokenRejected):
            verify_resource_token(value, config)


def test_missing_config_rejected():
    with pytest.raises(ValueError):
        ResourceAuthConfig("", "https://sonny.example/mcp", "public key")
