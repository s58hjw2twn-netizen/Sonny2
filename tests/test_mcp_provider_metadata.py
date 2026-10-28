import pytest
from sonny.mcp_provider_metadata import validate_provider, validate_chatgpt_client_registration

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


def test_chatgpt_cimd_requires_registration_and_supported_auth_method():
    metadata = {**VALID,
                "client_id_metadata_document_supported": True,
                "token_endpoint_auth_methods_supported": ["private_key_jwt"]}
    assert validate_chatgpt_client_registration(metadata) == "private_key_jwt"
    with pytest.raises(ValueError, match="CIMD"):
        validate_chatgpt_client_registration(
            {**metadata, "client_id_metadata_document_supported": False}
        )
    with pytest.raises(ValueError, match="supported token"):
        validate_chatgpt_client_registration(
            {**metadata, "token_endpoint_auth_methods_supported": ["client_secret_post"]}
        )


def test_chatgpt_dcr_requires_https_registration_endpoint():
    metadata = {**VALID,
                "registration_endpoint": ISSUER + "/register",
                "token_endpoint_auth_methods_supported": ["none"]}
    assert validate_chatgpt_client_registration(metadata, mode="dcr") == "none"
    with pytest.raises(ValueError, match="HTTPS"):
        validate_chatgpt_client_registration(
            {**metadata, "registration_endpoint": "http://auth.example/register"},
            mode="dcr",
        )
    with pytest.raises(ValueError, match="required"):
        validate_chatgpt_client_registration(
            {**metadata, "registration_endpoint": None}, mode="dcr"
        )


def test_chatgpt_registration_rejects_missing_auth_method_metadata():
    with pytest.raises(ValueError, match="must be advertised"):
        validate_chatgpt_client_registration(VALID)
    with pytest.raises(ValueError, match="Unsupported"):
        validate_chatgpt_client_registration(
            {**VALID, "token_endpoint_auth_methods_supported": ["none"]},
            mode="unknown",
        )
