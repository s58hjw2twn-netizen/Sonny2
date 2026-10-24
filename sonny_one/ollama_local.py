"""Dormant local Ollama text adapter. No model download or auto-activation.

Uses loopback HTTP only; rejects redirects and oversized responses. Never
connect this to a public route without separate owner authorization.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request as URLRequest, build_opener

from sonny_one.inference import InferenceFailure, InferenceTimeout, Request, Response


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LocalOllamaProvider:
    def __init__(self, model: str, *, endpoint: str = "http://127.0.0.1:11434"):
        if not isinstance(model, str) or not 1 <= len(model) <= 128 or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-" for c in model
        ):
            raise ValueError("Invalid local model name")
        if endpoint not in ("http://127.0.0.1:11434", "http://localhost:11434"):
            raise ValueError("Only the default local Ollama endpoint is permitted")
        self.model = model
        self.endpoint = endpoint
        self._opener = build_opener(_NoRedirect())

    def generate(self, request: Request) -> Response:
        payload = json.dumps({
            "model": self.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {"num_predict": 512},
        }).encode("utf-8")
        outgoing = URLRequest(
            self.endpoint + "/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(outgoing, timeout=request.timeout_seconds) as incoming:
                if incoming.status != 200:
                    raise InferenceFailure("Local model unavailable")
                raw = incoming.read(65537)
        except (TimeoutError,) as exc:
            raise InferenceTimeout("Inference timed out") from exc
        except (HTTPError, URLError, OSError) as exc:
            raise InferenceFailure("Local model unavailable") from exc
        if len(raw) > 65536:
            raise InferenceFailure("Local model response too large")
        try:
            data = json.loads(raw)
        except (UnicodeDecodeError, ValueError, TypeError) as exc:
            raise InferenceFailure("Invalid local model response") from exc
        if not isinstance(data, dict) or not data.get("done") or not isinstance(data.get("response"), str):
            raise InferenceFailure("Invalid local model response")
        if not data["response"].strip() or len(data["response"]) > 16000:
            raise InferenceFailure("Invalid local model response")
        return Response(text=data["response"], model_id=self.model, demo=False)
