import os
import time
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .store import Store
from .core import respond, CORE_VERSION


app = FastAPI(title="Sonny Assistant", version="0.1.0")
store = Store(os.getenv("SONNY_DB", "sonny.db"))


class UserIn(BaseModel):
    name: str


class ProjectIn(BaseModel):
    name: str
    goal: str


class ChatIn(BaseModel):
    message: str


class MemoryIn(BaseModel):
    value: str
    type: str = "fact"


class CorrectionIn(BaseModel):
    value: str


class ActionIn(BaseModel):
    action_text: str
    reason: str = "Sonny next step"
    source_response_id: str | None = None


class FeedbackIn(BaseModel):
    status: str


def user(x_user_id: str | None):
    if not x_user_id:
        raise HTTPException(401, "X-User-ID required")
    return x_user_id


def require_project(u, pid):
    p = store.project(u, pid)
    if not p:
        raise HTTPException(404)
    return p


# ---------------------------------------------------------
# SONNY WEB HOMEPAGE
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Sonny Assistant</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Helvetica,
                Arial,
                sans-serif;

            background:
                radial-gradient(
                    circle at top,
                    #263247 0%,
                    #111827 45%,
                    #080c14 100%
                );

            color: #f9fafb;
        }

        .card {
            width: 100%;
            max-width: 650px;

            background: rgba(31, 41, 55, 0.94);

            border: 1px solid #374151;
            border-radius: 26px;

            padding: 34px;

            box-shadow:
                0 25px 70px rgba(0, 0, 0, 0.45);
        }

        .badge {
            display: inline-block;

            padding: 7px 12px;

            border-radius: 999px;

            background: #f97316;
            color: white;

            font-size: 12px;
            font-weight: 800;

            letter-spacing: 0.6px;
        }

        h1 {
            margin-top: 18px;
            margin-bottom: 5px;

            font-size: clamp(36px, 9vw, 55px);
            line-height: 1;
        }

        .tagline {
            margin-top: 10px;

            font-size: 18px;
            color: #d1d5db;
        }

        .status {
            margin-top: 28px;

            display: flex;
            align-items: center;
            gap: 9px;

            font-weight: 700;
            color: #86efac;
        }

        .dot {
            width: 11px;
            height: 11px;

            border-radius: 50%;

            background: #22c55e;

            box-shadow:
                0 0 12px rgba(34, 197, 94, 0.8);
        }

        .panel {
            margin-top: 25px;

            padding: 20px;

            border-radius: 18px;

            background: #111827;

            border: 1px solid #374151;
        }

        .panel strong {
            color: #fb923c;
        }

        p {
            line-height: 1.6;
            color: #d1d5db;
        }

        .footer {
            margin-top: 24px;

            color: #9ca3af;
            font-size: 13px;
        }
    </style>
</head>

<body>

<div class="card">

    <span class="badge">
        SONNY ASSISTANT • BUILD 0.1.0
    </span>

    <h1>Sonny</h1>

    <div class="tagline">
        Your personal AI that learns how to work for you.
    </div>

    <div class="status">
        <span class="dot"></span>
        Sonny is online
    </div>

    <div class="panel">

        <strong>Deployment successful</strong>

        <p>
            Sonny Assistant is running on Railway.
        </p>

        <p>
            The Project Co-Pilot backend, persistent projects,
            memory controls, action tracking and Sonny core
            are available in this deployment.
        </p>

        <p>
            The interactive Sonny chat workspace is the next
            interface layer.
        </p>

    </div>

    <div class="footer">
        Sonny Assistant 0.1.0
    </div>

</div>

</body>
</html>
"""


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "ok": True,
        "build": "0.1.0",
        "core": CORE_VERSION
    }


# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------

@app.post("/users")
def users(b: UserIn):
    return {
        "user_id": store.create_user(b.name)
    }


# ---------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------

@app.post("/projects")
def projects(
    b: ProjectIn,
    x_user_id: str | None = Header(None)
):
    return {
        "project_id":
            store.create_project(
                user(x_user_id),
                b.name,
                b.goal
            )
    }


@app.get("/projects/{pid}")
def get_project(
    pid: str,
    x_user_id: str | None = Header(None)
):
    u = user(x_user_id)

    p = require_project(u, pid)

    return {
        "project": p,
        "confirmed_memories":
            store.memories(u, pid),
        "actions":
            store.actions(u, pid)
    }


# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

@app.post("/projects/{pid}/chat")
def chat(
    pid: str,
    b: ChatIn,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    p = require_project(u, pid)

    t = time.time()

    out = respond(
        p,
        store.memories(u, pid),
        b.message
    )

    rid = str(uuid.uuid4())

    latency = int(
        (time.time() - t) * 1000
    )

    store.trace(
        rid,
        u,
        pid,
        "stub-local",
        CORE_VERSION,
        p["state_version"],
        out["answer_state"],
        bool(out.get("memory_proposal")),
        bool(out.get("next_action")),
        latency,
        0.0
    )

    return {
        "response_id": rid,
        **out,
        "state_version":
            p["state_version"]
    }


# ---------------------------------------------------------
# MEMORY
# ---------------------------------------------------------

@app.post("/projects/{pid}/memories")
def propose_memory(
    pid: str,
    b: MemoryIn,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    require_project(u, pid)

    m = store.propose_memory(
        u,
        pid,
        b.value,
        b.type
    )

    return {
        "memory_id": m,
        "status": "PROPOSED"
    }


@app.post(
    "/projects/{pid}/memories/{mid}/confirm"
)
def confirm(
    pid: str,
    mid: str,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    require_project(u, pid)

    if not store.confirm_memory(
        u,
        pid,
        mid
    ):
        raise HTTPException(404)

    return {
        "confirmed": True
    }


@app.post(
    "/projects/{pid}/memories/{mid}/correct"
)
def correct(
    pid: str,
    mid: str,
    b: CorrectionIn,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    require_project(u, pid)

    n = store.correct_memory(
        u,
        pid,
        mid,
        b.value
    )

    if not n:
        raise HTTPException(404)

    return {
        "memory_id": n,
        "status": "CONFIRMED"
    }


@app.delete(
    "/projects/{pid}/memories/{mid}"
)
def delete(
    pid: str,
    mid: str,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    require_project(u, pid)

    if not store.delete_memory(
        u,
        pid,
        mid
    ):
        raise HTTPException(404)

    return {
        "deleted": True
    }


# ---------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------

@app.post("/projects/{pid}/actions")
def action(
    pid: str,
    b: ActionIn,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    require_project(u, pid)

    a = store.propose_action(
        u,
        pid,
        b.action_text,
        b.reason,
        b.source_response_id
    )

    return {
        "action_id": a,
        "status": "PROPOSED"
    }


@app.post(
    "/projects/{pid}/actions/{aid}/feedback"
)
def feedback(
    pid: str,
    aid: str,
    b: FeedbackIn,
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

    require_project(u, pid)

    if not store.action_feedback(
        u,
        pid,
        aid,
        b.status
    ):
        raise HTTPException(404)

    return {
        "recorded": True
    }
