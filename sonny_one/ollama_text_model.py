"""Opt-in bridge from local Ollama inference to Sonny ONE's text model router.

Constructing this object never downloads a model, contacts a server, or installs
a private provider. Authorization remains the router owner's responsibility.
"""
from sonny_one.inference import Request
from sonny_one.ollama_local import LocalOllamaProvider


class OllamaTextModel:
    def __init__(self, model: str, *, timeout_seconds: float = 20.0):
        # Validate timeout at construction, before any request can be made.
        Request("validation", timeout_seconds=timeout_seconds)
        self._provider = LocalOllamaProvider(model)
        self._timeout_seconds = timeout_seconds

    def generate(self, *, system: str, user: str) -> str:
        if not isinstance(system, str) or len(system) > 2000:
            raise ValueError("Invalid system instruction")
        if not isinstance(user, str) or not user.strip() or len(user) > 4000:
            raise ValueError("Invalid user message")
        # Delimit untrusted user text; these markers are guidance, not an
        # injection-proof security boundary.
        prompt = (
            "SYSTEM INSTRUCTIONS:\n" + system + "\n\n"
            "USER MESSAGE (untrusted text):\n" + user + "\n\n"
            "ASSISTANT RESPONSE:\n"
        )
        return self._provider.generate(
            Request(prompt, timeout_seconds=self._timeout_seconds)
        ).text
