import httpx
import pytest

from sonny.gemini_provider import generate_gemini


class StubClient:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.last = None

    def post(self, url, **kwargs):
        self.last = (url, kwargs)
        return httpx.Response(self.status, json=self.payload, request=httpx.Request("POST", url))


def test_gemini_maps_history_and_extracts_text(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = StubClient({"candidates": [{"content": {"parts": [{"text": "Hello from Sonny"}]}}]})
    result = generate_gemini("Be Sonny", [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}], "Next", client=client)
    assert result == "Hello from Sonny"
    url, options = client.last
    assert "gemini-" in url
    assert options["headers"]["x-goog-api-key"] == "test-key"
    assert [t["role"] for t in options["json"]["contents"]] == ["user", "model", "user"]
    assert options["json"]["systemInstruction"]["parts"][0]["text"] == "Be Sonny"


def test_gemini_requires_server_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        generate_gemini("instructions", [], "hello", client=StubClient({}))


def test_gemini_surfaces_http_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    with pytest.raises(httpx.HTTPStatusError):
        generate_gemini("instructions", [], "hello", client=StubClient({"error": "denied"}, 403))
