"""Server-side-only Gemini HTTPS transport, not activated by provider config.

This module never reads credentials from disk or environment, and is not
imported by the public Safari demo. The caller must explicitly provide a
server-side API key and opt in to sending a request. Do not use this transport
with paid projects or without verifying provider-side quota/billing controls.
"""
import json
import socket
import ssl
from urllib import error, request
from urllib.parse import quote

from sonny_one.gemini_request import GeminiRequestConfig, build_gemini_request
from sonny_one.gemini_response import parse_gemini_response
from sonny_one.inference import InferenceFailure, InferenceTimeout, Request, Response


class GeminiTransport:
    """Bounded synchronous transport for an explicitly approved server process."""

    def __init__(self, *, api_key: str, model_id: str = "gemini-2.5-flash-lite",
                 opener=None):
        if not isinstance(api_key, str) or not 8 <= len(api_key) <= 256 or any(c.isspace() for c in api_key):
            raise ValueError("Invalid server-side API key")
        if not isinstance(model_id, str) or not model_id or len(model_id) > 128 or not all(c.isalnum() or c in "-_." for c in model_id):
            raise ValueError("Invalid model ID")
        self._api_key = api_key
        self._model_id = model_id
        self._opener = opener or request.urlopen

    def generate(self, incoming: Request) -> Response:
        if not isinstance(incoming, Request):
            raise TypeError("Expected validated request")
        config = GeminiRequestConfig(model_id=self._model_id)
        body = json.dumps(build_gemini_request(incoming.prompt, config), separators=(",", ":")).encode("utf-8")
        url = "https://generativelanguage.googleapis.com/v1beta/models/" + quote(self._model_id, safe="") + ":generateContent"
        req = request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }, method="POST")
        try:
            with self._opener(req, timeout=min(incoming.timeout_seconds, 20.0), context=ssl.create_default_context()) as response:
                if getattr(response, "status", 200) != 200:
                    raise InferenceFailure("Inference unavailable")
                raw = response.read(65537)
                if len(raw) > 65536:
                    raise InferenceFailure("Inference unavailable")
        except (TimeoutError, socket.timeout) as exc:
            raise InferenceTimeout("Inference timed out") from exc
        except (error.HTTPError, error.URLError, OSError, ValueError) as exc:
            raise InferenceFailure("Inference unavailable") from exc
        try:
            return parse_gemini_response(json.loads(raw), model_id=self._model_id)
        except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InferenceFailure("Inference unavailable") from exc
