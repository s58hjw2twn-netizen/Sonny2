"""Local, stateless demo. No model providers, credentials, or research execution."""
from pathlib import Path
import re

from sonny_one.inference import InferenceFailure, InferenceTimeout
from sonny_one.inference_config import InferenceSettings, build_provider
from sonny_one.inference_async import generate_with_deadline
from sonny_one.rate_limit import LocalRateLimiter
from sonny_one.concurrency_gate import LocalConcurrencyGate
from sonny_one.private_provider import get_private_provider
from sonny_one.global_quota import GlobalRequestQuota
from sonny_one.outstanding_provider_gate import OutstandingProviderGate

from fastapi import Depends, FastAPI, Header, HTTPException
from sonny.auth import authenticated_user
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

WEB = Path(__file__).with_name("web")
private_limiter = LocalRateLimiter(limit=30, window_seconds=60)
private_concurrency = LocalConcurrencyGate(max_active=4)
private_global_quota = GlobalRequestQuota(max_requests=100)
private_provider_gate = OutstandingProviderGate(capacity=2)


def private_authenticated_user(authorization: str | None = Header(None)) -> str:
    try:
        return authenticated_user(authorization)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Authentication unavailable") from exc
app = FastAPI(title="Sonny ONE local demo", docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=WEB), name="assets")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    goal: str = Field(default="Build a useful personal assistant", max_length=500)
    memories: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Write a message first")
        return value.strip()

    @field_validator("memories")
    @classmethod
    def bounded_memories(cls, values: list[str]) -> list[str]:
        if any(not v.strip() or len(v) > 500 for v in values):
            raise ValueError("Each approved memory must contain 1–500 characters")
        return values


@app.middleware("http")
async def demo_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def home():
    return FileResponse(WEB / "index.html")


@app.get("/sw.js")
def service_worker():
    return FileResponse(WEB / "sw.js", media_type="application/javascript")


@app.get("/api/status")
def status():
    return {"mode": "deterministic-demo", "model_connected": False, "api_cost": 0,
            "server_persistence": False}


@app.post("/api/inference/demo")
async def inference_demo(body: ChatRequest):
    """Explicit offline adapter route, separate from the legacy deterministic chat."""
    try:
        result = await generate_with_deadline(build_provider(InferenceSettings()), body.message, timeout_seconds=5.0)
    except InferenceTimeout as exc:
        raise HTTPException(status_code=504, detail="Inference timed out") from exc
    except InferenceFailure as exc:
        raise HTTPException(status_code=503, detail="Inference unavailable") from exc
    return {"text": result.text, "mode": "deterministic-demo",
            "model_id": result.model_id, "model_connected": not result.demo}


@app.post("/api/inference/private")
async def private_inference(body: ChatRequest, user_id: str = Depends(private_authenticated_user)):
    """Authenticated private inference; external providers remain disabled by default."""
    if not private_limiter.allow(user_id):
        raise HTTPException(status_code=429, detail="Request limit exceeded", headers={"Retry-After": "60"})
    if not private_concurrency.acquire():
        raise HTTPException(status_code=503, detail="Inference capacity reached", headers={"Retry-After": "1"})
    try:
        if not private_global_quota.allow():
            raise HTTPException(status_code=429, detail="Global inference budget exhausted", headers={"Retry-After": "3600"})
        try:
            result = await private_provider_gate.run(get_private_provider(), body.message, timeout_seconds=5.0)
        except InferenceTimeout as exc:
            raise HTTPException(status_code=504, detail="Inference timed out") from exc
        except InferenceFailure as exc:
            raise HTTPException(status_code=503, detail="Inference unavailable") from exc
        return {"text": result.text, "mode": "deterministic-demo" if result.demo else "private-inference",
                "model_id": result.model_id, "model_connected": not result.demo}
    finally:
        private_concurrency.release()


@app.post("/api/chat")
def chat(body: ChatRequest):
    message = body.message.lower()
    words = set(re.findall(r"[a-z]+", message))
    if (words & {"remember", "memory", "memories"} or "know about me" in message):
        text = ("Your approved memories:\n" + "\n".join(f"• {m}" for m in body.memories)
                if body.memories else "You have no approved memories. Add a fact in the memory panel and explicitly save it to use it here.")
    elif words & {"plan", "next", "goal", "help"}:
        text = (f"Let's work toward: {body.goal or 'your next goal'}.\n\n"
                "1. Choose one small outcome you can finish today.\n"
                "2. Write down its main constraint.\n"
                "3. Complete the smallest step and check the result.\n\n"
                "This is a fixed demo plan, not a model-generated recommendation.")
    elif words & {"hello", "hi", "hey"}:
        text = "Hi, I'm Sonny ONE. Try ‘Help me plan’ or ‘What do you remember?’ to explore this local demo."
    else:
        text = ("This demo supports planning and approved-memory recall. A language model is not connected yet, "
                "so I can't answer that request here. Try ‘Help me plan’ or ‘What do you remember?’.")
    return {"text": text, "mode": "deterministic-demo", "memory_count": len(body.memories)}
