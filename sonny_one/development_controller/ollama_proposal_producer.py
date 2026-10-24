"""Optional loopback-only Ollama coding proposal producer.

No model is installed or started by this module. The caller must explicitly
opt in to an already-running local Ollama service and a locally available model.
The response remains an untrusted review-only proposal, validated separately
by ModelProposalAdapter. No credentials or external provider API are used.
"""
from __future__ import annotations

import json
import re
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
_ENDPOINT = "http://127.0.0.1:11434/api/generate"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirects forbidden")


class OllamaProposalProducer:
    def __init__(self, *, model: str, enabled: bool = False, timeout: int = 45):
        if not isinstance(model, str) or not _MODEL.fullmatch(model):
            raise ValueError("invalid local model name")
        if type(timeout) is not int or not 1 <= timeout <= 120:
            raise ValueError("invalid timeout")
        self.model = model
        self.enabled = enabled is True
        self.timeout = timeout

    def __call__(self, task: dict) -> dict:
        if not self.enabled:
            raise PermissionError("local model calls require explicit opt-in")
        if not isinstance(task, dict) or task.get("id") != "RES-001":
            raise PermissionError("only RES-001 research proposals allowed")
        if task.get("state") != "ready" or task.get("requires_approval") is not False:
            raise PermissionError("task not authorized")
        prompt = (
            "You are proposing a research-only unified diff. Output JSON only "
            'with keys "task_id" (value "RES-001") and "patch_text". '
            "Do not execute code, request credentials, change policy, or deploy. "
            "The ONLY editable path is sonny_one/apl_targets/offline_strategy.py. "
            "Use a unified git diff with diff --git, --- and +++ headers. "
            "Keep the change minimal. Your output will be rejected if unsafe."
        )
        body = json.dumps({"model": self.model, "prompt": prompt,
                           "stream": False, "format": "json",
                           "options": {"temperature": 0, "num_predict": 1024}}).encode()
        request = Request(_ENDPOINT, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=self.timeout) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("local model response too large")
        outer = json.loads(raw)
        if not isinstance(outer, dict) or not isinstance(outer.get("response"), str):
            raise ValueError("invalid Ollama response")
        inner = json.loads(outer["response"])
        if not isinstance(inner, dict) or set(inner) != {"task_id", "patch_text"}:
            raise ValueError("invalid model proposal schema")
        return inner
