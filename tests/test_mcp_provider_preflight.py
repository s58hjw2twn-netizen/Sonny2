"""No live external requests; checks trusted metadata preflight behavior."""
import io
import json

import pytest

from sonny import mcp_provider_preflight as preflight


ISSUER = "https://auth.example"
URL = ISSUER + "/.well-known/oauth-authorization-server"
VALID = {
    "issuer": ISSUER,
    "authorization_endpoint": ISSUER + "/authorize",
    "token_endpoint": ISSUER + "/token",
    "jwks_uri": ISSUER + "/keys",
    "response_types_supported": ["code"],
    "code_challenge_methods_supported": ["S256"],
}


class Response:
    status = 200

    def __init__(self, payload):
        self.stream = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, count):
        return self.stream.read(count)


def test_preflight_fetches_and_validates_provider(monkeypatch):
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == URL
            assert timeout == 5
            return Response(json.dumps(VALID).encode())

    monkeypatch.setattr(preflight, "build_opener", lambda *args: Opener())
    assert preflight.fetch_provider_metadata(URL, ISSUER)["jwks_uri"] == ISSUER + "/keys"


@pytest.mark.parametrize("url", [
    "http://auth.example/metadata",
    "https://other.example/metadata",
    "https://auth.example:444/metadata",
    "https://user:pass@auth.example/metadata",
    "https://auth.example/metadata?token=secret",
])
def test_preflight_rejects_untrusted_source_before_network(monkeypatch, url):
    def forbidden(*args):
        raise AssertionError("network access must not occur")

    monkeypatch.setattr(preflight, "build_opener", forbidden)
    with pytest.raises(ValueError):
        preflight.fetch_provider_metadata(url, ISSUER)


def test_preflight_rejects_oversized_metadata(monkeypatch):
    class Opener:
        def open(self, request, timeout):
            return Response(b"x" * 65537)

    monkeypatch.setattr(preflight, "build_opener", lambda *args: Opener())
    with pytest.raises(ValueError, match="size limit"):
        preflight.fetch_provider_metadata(URL, ISSUER)


def test_preflight_rejects_issuer_mismatch(monkeypatch):
    class Opener:
        def open(self, request, timeout):
            return Response(json.dumps({**VALID, "issuer": "https://other.example"}).encode())

    monkeypatch.setattr(preflight, "build_opener", lambda *args: Opener())
    with pytest.raises(ValueError, match="issuer"):
        preflight.fetch_provider_metadata(URL, ISSUER)
