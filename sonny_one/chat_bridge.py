"""Read-only, token-gated local Sonny ONE Chat Bridge prototype.

No model calls, user memory, repository writes, or remote GitHub access.
Runtime evidence must be supplied by a trusted operator, never by a caller.
"""
import hmac
import os
import re
from fastapi import Depends, FastAPI, Header, HTTPException
from sonny_one.capability_inventory import capability_inventory

SHA = re.compile(r"^[0-9a-f]{40}$")


def create_app(*, token=None, verified_sha=None):
    secret = token if token is not None else os.getenv("SONNY_CHAT_BRIDGE_TOKEN", "")
    if not isinstance(secret, str) or len(secret) < 32:
        raise RuntimeError("SONNY_CHAT_BRIDGE_TOKEN must contain at least 32 characters")
    revision = verified_sha if verified_sha is not None else os.getenv("SONNY_CHAT_BRIDGE_VERIFIED_SHA", "")
    if revision and not SHA.fullmatch(revision):
        raise RuntimeError("Verified SHA must be a full lowercase commit hash")
    app = FastAPI(title="Sonny ONE read-only Chat Bridge", docs_url=None, redoc_url=None, openapi_url=None)

    def require_token(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        supplied = authorization[7:]
        if not hmac.compare_digest(supplied, secret):
            raise HTTPException(status_code=401, detail="Authentication required")

    @app.middleware("http")
    async def private_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/v1/status", dependencies=[Depends(require_token)])
    def status():
        return {
            "service": "sonny-one-chat-bridge",
            "mode": "read_only",
            "verified_revision": revision or None,
            "revision_attestation": "operator_supplied_not_independently_checked" if revision else "unavailable",
            "runtime_tests_verified": False,
            "external_actions_enabled": False,
            "memory_access_enabled": False,
            "autonomous_commits_enabled": False,
        }

    @app.get("/v1/capabilities", dependencies=[__import__("fastapi").Depends(require_token)])
    def capabilities():
        return {"source": "static_inventory_not_live_proof", "capabilities": capability_inventory()}

    return app
