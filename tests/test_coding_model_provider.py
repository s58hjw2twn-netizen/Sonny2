"""Tests use a simulated provider response; no paid API request."""
import json
import httpx
import pytest

from sonny.coding_model_provider import generate_and_stage_patch
from sonny.research_agent import Task


class StubClient:
    def __init__(self, response_text):
        self.response_text = response_text
        self.calls = 0

    def post(self, url, **kwargs):
        self.calls += 1
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": self.response_text}]}}]},
            request=httpx.Request("POST", url),
        )


def test_generated_patch_stages_without_commit(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    response = json.dumps({
        "path": "sonny/example.py",
        "content": "value = 2\n",
        "reason": "Update the example value",
    })
    client = StubClient(response)
    task = Task("G1", "Update the value", ("sonny/example.py",), "low")
    staged = generate_and_stage_patch(task, {"sonny/example.py": "value = 1\n"}, client=client)
    assert client.calls == 1
    assert staged["candidate"]["sonny/example.py"] == "value = 2\n"
    assert staged["provider"] == "gemini"
    assert staged["writes_performed"] == 0
    assert staged["execution_allowed"] is False
    assert staged["independently_verified"] is False
    assert staged["commit_allowed"] is False


def test_rejects_protected_target_before_provider_call(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    client = StubClient("{}")
    task = Task("G2", "Alter gate", ("sonny/model_patch_gate.py",), "low")
    with pytest.raises(ValueError, match="safety controls"):
        generate_and_stage_patch(task, {"sonny/model_patch_gate.py": "x = 1"}, client=client)
    assert client.calls == 0


def test_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    task = Task("G3", "Update value", ("sonny/example.py",), "low")
    with pytest.raises(RuntimeError, match="not configured"):
        generate_and_stage_patch(task, {"sonny/example.py": "value = 1\n"}, client=StubClient("{}"))


def test_rejects_malformed_generated_source(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    response = json.dumps({"path": "sonny/example.py", "content": "def broken(:", "reason": "bad"})
    task = Task("G4", "Update value", ("sonny/example.py",), "low")
    with pytest.raises(ValueError, match="syntactically valid Python"):
        generate_and_stage_patch(task, {"sonny/example.py": "value = 1\n"}, client=StubClient(response))
