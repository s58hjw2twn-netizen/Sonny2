"""Provider-neutral inference interface for Sonny ONE (offline-only default)."""
from dataclasses import dataclass
from typing import Protocol


class InferenceFailure(Exception):
    """Safe, public-facing inference failure."""


@dataclass(frozen=True)
class Request:
    prompt: str

    def __post_init__(self):
        if not isinstance(self.prompt, str) or not self.prompt.strip() or len(self.prompt) > 8000:
            raise ValueError("Prompt must be between 1 and 8000 characters")


@dataclass(frozen=True)
class Response:
    text: str
    model_id: str
    demo: bool = True


class Provider(Protocol):
    def generate(self, request: Request) -> Response: ...


class OfflineProvider:
    def generate(self, request: Request) -> Response:
        return Response("Sonny ONE is in offline demo mode. No language model is connected.", "offline-demo-v1")


def generate(provider: Provider, prompt: str) -> Response:
    request = Request(prompt)
    try:
        result = provider.generate(request)
    except Exception as exc:
        raise InferenceFailure("Inference unavailable") from exc
    if not isinstance(result, Response) or not isinstance(result.text, str) or not result.text.strip():
        raise InferenceFailure("Invalid provider response")
    if not isinstance(result.model_id, str) or not result.model_id.strip() or len(result.model_id) > 128:
        raise InferenceFailure("Invalid model identifier")
    if len(result.text) > 16000 or not isinstance(result.demo, bool):
        raise InferenceFailure("Invalid provider response")
    return result
