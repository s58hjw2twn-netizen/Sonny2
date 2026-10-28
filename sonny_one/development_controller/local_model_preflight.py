"""Read-only preflight for an explicitly enabled local Ollama runtime.

This module never installs models, downloads weights, starts services, or
invokes inference. The endpoint is fixed to IPv4 loopback. A successful
preflight proves only that the local API listed the requested model.
"""
from __future__ import annotations

import json
from urllib.request import HTTPRedirectHandler, Request, build_opener, ProxyHandler

from sonny_one.development_controller.ollama_proposal_producer import _MODEL

_ENDPOINT = "http://127.0.0.1:11434/api/tags"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect forbidden")


def check_local_model(model: str, *, enabled: bool = False,
                      timeout: int = 5) -> dict:
    if enabled is not True:
        raise PermissionError("explicit local-model opt-in required")
    if not isinstance(model, str) or not _MODEL.fullmatch(model):
        raise ValueError("invalid model name")
    if type(timeout) is not int or not 1 <= timeout <= 15:
        raise ValueError("invalid timeout")
    request = Request(_ENDPOINT, method="GET", headers={
        "Accept": "application/json",
    })
    with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=timeout) as response:
        raw = response.read(131073)
    if len(raw) > 131072:
        raise ValueError("local model list too large")
    payload = json.loads(raw)
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        raise ValueError("invalid local model list")
    available = any(
        isinstance(item, dict) and item.get("name") == model
        for item in models
    )
    return {"endpoint": "127.0.0.1:11434", "model": model,
            "available": available, "inference_tested": False,
            "model_downloaded": False, "cost_incurred": False}
