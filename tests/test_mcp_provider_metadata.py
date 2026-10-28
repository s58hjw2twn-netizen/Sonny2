import pytest
from sonny.mcp_provider_metadata import validate_provider

ISSUER = "https://auth.example"
VALID = {
    "issuer": ISSUER,
    "authorization_endpoint": ISSUER + "/authorize",
    "token_endpoint": ISSUER + "/token",
    "jwks_uri": ISSUER + "/keys",
    "response_types_supported": ["code"],
    "code_challenge_methods_supported": ["S256"],
}


def test_accepts_code_pkce_provider():
    result = validate_provider(VALID, ISSUER)
    assert result["jwks_uri"] == ISSUER + "/keys"


@pytest.mark.parametrize("change", [
    {"issuer": "https://other.example"},
    {"authorization_endpoint": "http://auth.example/authorize"},
    {"token_endpoint": "https://user:pass@auth.example/token"},
    {"jwks_uri": "http://auth.example/keys"},
    {"jwks_uri": None},
    {"response_types_supported": ["token"]},
    {"code_challenge_methods_supported": ["plain"]},
])
def test_rejects_invalid_provider(change):
    with pytest.raises(ValueError):
        validate_provider({**VALID, **change}, ISSUER)


def test_rejects_non_object_metadata():
    with pytest.raises(ValueError):
        validate_provider(None, ISSUER)
