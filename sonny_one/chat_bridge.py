"""Read-only, token-gated local Sonny ONE Chat Bridge prototype.

No model calls, user memory, repository writes, or remote GitHub access.
Runtime evidence must be supplied by a trusted operator, never by a caller.
"""
import hmac
import os
import threading
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
    credentials = {"active": secret}
    credential_lock = threading.Lock()
    app = FastAPI(title="Sonny ONE read-only Chat Bridge", docs_url=None, redoc_url=None, openapi_url=None)

    def require_token(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        supplied = authorization[7:]
        with credential_lock:
            active = credentials["active"]
        if not hmac.compare_digest(supplied, active):
            raise HTTPException(status_code=401, detail="Authentication required")

    @app.middleware("http")
    async def private_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def rotate_credential(*, current_token: str, replacement_token: str) -> None:
        """Operator-only local control, never exposed as an HTTP endpoint.

        Rotation immediately invalidates the prior token for future requests.
        Callers must use a trusted operator channel; this does not persist across restart.
        """
        if not isinstance(replacement_token, str) or len(replacement_token) < 32:
            raise ValueError("Replacement token must contain at least 32 characters")
        with credential_lock:
            if not hmac.compare_digest(current_token, credentials["active"]):
                raise PermissionError("Invalid current credential")
            credentials["active"] = replacement_token

    app.state.rotate_credential = rotate_credential

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
