import os
import time
import uuid

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .store import Store
from .identity_store import IdentityStore
from .sessions import SessionStore
from .login_throttle import LoginThrottle
from .core import respond, CORE_VERSION


app = FastAPI(title="Sonny Assistant", version="0.1.0")
store = Store(os.getenv("SONNY_DB", "sonny.db"))
identities = IdentityStore(store.db)
identities.initialize()
sessions = SessionStore(store.db)
sessions.initialize()
login_throttle = LoginThrottle(store.db)
login_throttle.initialize()


class LoginIn(BaseModel):
    user_id: str
    password: str


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


def authenticated_user(request: Request):
    token = request.cookies.get("sonny_session")
    uid = sessions.resolve(token)
    if not uid:
        raise HTTPException(401, "Authentication required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not sessions.valid_csrf(token, request.headers.get("X-CSRF-Token")):
            raise HTTPException(403, "CSRF validation failed")
        origin = request.headers.get("origin")
        if origin:
            expected = str(request.base_url).rstrip("/")
            if origin.rstrip("/") != expected:
                raise HTTPException(403, "Invalid origin")
    return uid


def check_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Invalid origin")


def secure_cookie(request: Request):
    # Reverse proxies must forward HTTPS correctly; never expose cookies over
    # HTTP except explicitly enabled local development.
    if request.url.scheme != "https":
        peer = request.client.host if request.client else ""
        if os.getenv("SONNY_ALLOW_HTTP_LOCAL") != "1" or peer not in {
            "127.0.0.1", "::1", "testclient"
        }:
            raise HTTPException(503, "HTTPS required for authentication")
    return request.url.scheme == "https"


def require_project(u, pid):
    p = store.project(u, pid)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


# ---------------------------------------------------------
# SONNY WEB APP
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0,
    viewport-fit=cover"
>

<meta name="theme-color" content="#080c14">

<title>Sonny Assistant</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    min-height: 100%;
}

body {
    min-height: 100vh;

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
            #111827 42%,
            #080c14 100%
        );

    color: #f9fafb;
}

.app {
    width: 100%;
    max-width: 760px;

    min-height: 100vh;

    margin: 0 auto;
    padding:
        max(24px, env(safe-area-inset-top))
        18px
        max(30px, env(safe-area-inset-bottom));
}

.header {
    padding: 14px 4px 20px;
}

.badge {
    display: inline-block;

    padding: 7px 12px;

    border-radius: 999px;

    background: #f97316;

    color: white;

    font-size: 11px;
    font-weight: 800;

    letter-spacing: .7px;
}

h1 {
    margin: 15px 0 4px;

    font-size: 42px;
    line-height: 1;
}

.tagline {
    color: #cbd5e1;
    line-height: 1.45;
}

.status {
    margin-top: 15px;

    display: flex;
    align-items: center;
    gap: 8px;

    color: #86efac;

    font-size: 14px;
    font-weight: 700;
}

.dot {
    width: 10px;
    height: 10px;

    border-radius: 50%;

    background: #22c55e;

    box-shadow:
        0 0 12px rgba(34, 197, 94, .85);
}

.card {
    background: rgba(31, 41, 55, .94);

    border: 1px solid #374151;

    border-radius: 22px;

    box-shadow:
        0 20px 60px rgba(0, 0, 0, .35);
}

.setup {
    padding: 20px;
    margin-bottom: 18px;
}

.setup-title {
    font-size: 15px;
    font-weight: 800;

    margin-bottom: 13px;
}

.row {
    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 10px;
}

input,
textarea,
button {
    font: inherit;
}

input,
textarea {
    width: 100%;

    padding: 13px 14px;

    border-radius: 13px;

    border: 1px solid #475569;

    outline: none;

    background: #111827;

    color: #f8fafc;
}

input:focus,
textarea:focus {
    border-color: #f97316;
}

textarea {
    resize: none;

    min-height: 52px;
    max-height: 160px;
}

button {
    border: 0;

    border-radius: 13px;

    cursor: pointer;

    font-weight: 800;
}

.primary {
    background: #f97316;
    color: white;

    padding: 13px 16px;
}

.primary:disabled {
    opacity: .55;
    cursor: default;
}

.secondary {
    background: #334155;
    color: #e2e8f0;

    padding: 12px 14px;
}

.workspace {
    overflow: hidden;
}

.workspace-top {
    display: flex;

    justify-content: space-between;
    align-items: center;

    gap: 12px;

    padding: 17px 18px;

    border-bottom: 1px solid #374151;
}

.project-name {
    font-weight: 800;
}

.project-goal {
    margin-top: 3px;

    color: #94a3b8;

    font-size: 12px;
}

.chat {
    min-height: 320px;
    max-height: 55vh;

    overflow-y: auto;

    padding: 20px 16px;

    display: flex;
    flex-direction: column;

    gap: 14px;
}

.empty {
    margin: auto;

    max-width: 420px;

    text-align: center;

    color: #94a3b8;

    line-height: 1.55;
}

.message {
    max-width: 88%;

    padding: 13px 15px;

    border-radius: 17px;

    line-height: 1.48;

    white-space: pre-wrap;
    word-wrap: break-word;
}

.message.user {
    align-self: flex-end;

    background: #f97316;

    color: white;

    border-bottom-right-radius: 5px;
}

.message.sonny {
    align-self: flex-start;

    background: #111827;

    border: 1px solid #374151;

    color: #e5e7eb;

    border-bottom-left-radius: 5px;
}

.label {
    display: block;

    margin-bottom: 5px;

    font-size: 10px;
    font-weight: 900;

    letter-spacing: .7px;

    opacity: .65;
}

.composer {
    padding: 14px;

    border-top: 1px solid #374151;

    display: grid;

    grid-template-columns:
        minmax(0, 1fr) auto;

    gap: 10px;

    align-items: end;
}

.send {
    height: 52px;

    padding: 0 18px;

    background: #f97316;

    color: white;
}

.send:disabled {
    opacity: .5;
}

.meta {
    padding: 0 18px 16px;

    color: #64748b;

    font-size: 11px;
}

.hidden {
    display: none;
}

.error {
    margin-top: 10px;

    color: #fca5a5;

    font-size: 13px;

    line-height: 1.4;
}

.footer {
    padding: 20px 4px 0;

    text-align: center;

    color: #64748b;

    font-size: 11px;
}

@media (max-width: 560px) {

    .app {
        padding-left: 12px;
        padding-right: 12px;
    }

    .row {
        grid-template-columns: 1fr;
    }

    .chat {
        min-height: 350px;
        max-height: 52vh;
    }

    .message {
        max-width: 92%;
    }

}

</style>
</head>

<body>

<div class="app">

    <header class="header">

        <span class="badge">
            SONNY ASSISTANT • BUILD 0.1.0
        </span>

        <h1>Sonny</h1>

        <div class="tagline">
            Your personal AI that learns how to work for you.
        </div>

        <div class="status">
            <span class="dot"></span>
            <span id="statusText">Sonny is online</span>
        </div>

    </header>


    <section
        id="setupCard"
        class="card setup"
    >

        <div class="setup-title">
            Sign in to your Sonny account
        </div>

        <div class="row">

            <input
                id="nameInput"
                placeholder="Your existing account ID"
                autocomplete="name"
            >

            <input
                id="passwordInput"
                type="password"
                autocomplete="current-password"
                placeholder="Password"
            >
            <input
                id="projectInput"
                placeholder="Project name"
                value="My Sonny Project"
            >

        </div>

        <div style="margin-top:10px">

            <input
                id="goalInput"
                placeholder="What do you want Sonny to help you accomplish?"
                value="Help me organize, think and take useful next steps."
            >

        </div>

        <div style="margin-top:12px">

            <button
                id="startButton"
                class="primary"
                onclick="startWorkspace()"
            >
                Sign in and start Sonny
            </button>

        </div>

        <div
            id="setupError"
            class="error hidden"
        ></div>

    </section>


    <section
        id="workspace"
        class="card workspace hidden"
    >

        <div class="workspace-top">

            <div>

                <div
                    id="projectName"
                    class="project-name"
                >
                    Sonny Project
                </div>

                <div
                    id="projectGoal"
                    class="project-goal"
                ></div>

            </div>

            <button
                class="secondary"
                onclick="resetWorkspace()"
            >
                Sign out
            </button>

        </div>


        <div
            id="chat"
            class="chat"
        >

            <div
                id="emptyState"
                class="empty"
            >
                <strong>
                    Sonny is ready.
                </strong>

                <br><br>

                Type a message below to start working
                on this project.
            </div>

        </div>


        <div class="composer">

            <textarea
                id="messageInput"
                placeholder="Message Sonny..."
                rows="1"
                onkeydown="composerKey(event)"
            ></textarea>

            <button
                id="sendButton"
                class="send"
                onclick="sendMessage()"
            >
                Send
            </button>

        </div>

        <div
            id="chatMeta"
            class="meta"
        >
            Project Co-Pilot • Sonny Core
        </div>

    </section>


    <div class="footer">
        Sonny Assistant 0.1.0
    </div>

</div>


<script>
function renderMarkdown(text) {

    const escaped = String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    return escaped
        .replace(
            /^### (.+)$/gm,
            "<strong>$1</strong>"
        )
        .replace(
            /^## (.+)$/gm,
            "<strong>$1</strong>"
        )
        .replace(
            /^# (.+)$/gm,
            "<strong>$1</strong>"
        )
        .replace(
            /\*\*(.+?)\*\*/g,
            "<strong>$1</strong>"
        )
        .replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
        )
        .replace(
            /\n/g,
            "<br>"
        );
}
const state = {
    userId: null,
    csrfToken: null,
    projectId: null,
    projectName: null,
    projectGoal: null
};


function apiHeaders() {

    const h = {
        "Content-Type": "application/json"
    };

    if (state.csrfToken) {
        h["X-CSRF-Token"] = state.csrfToken;
    }

    return h;
}


async function api(path, options = {}) {

    const response = await fetch(
        path,
        {
            ...options,
            credentials: "same-origin",
            headers: {
                ...apiHeaders(),
                ...(options.headers || {})
            }
        }
    );

    let data = null;

    try {
        data = await response.json();
    }
    catch (_) {
        data = {};
    }

    if (!response.ok) {

        const message =
            data.detail ||
            "Request failed.";

        throw new Error(
            typeof message === "string"
                ? message
                : JSON.stringify(message)
        );
    }

    return data;
}


function saveState() {

    localStorage.setItem(
        "sonny_workspace",
        JSON.stringify({projectId:state.projectId,projectName:state.projectName,projectGoal:state.projectGoal})
    );
}


function loadState() {

    try {

        const saved =
            JSON.parse(
                localStorage.getItem(
                    "sonny_workspace"
                )
            );

        if (
            saved &&
            saved.projectId &&
            state.csrfToken
        ) {

            Object.assign(
                state,
                saved
            );

            showWorkspace();

            return true;
        }

    }
    catch (_) {}

    return false;
}


async function showWorkspace() {

    document
        .getElementById("setupCard")
        .classList
        .add("hidden");

    document
        .getElementById("workspace")
        .classList
        .remove("hidden");

    document
        .getElementById("projectName")
        .textContent =
            state.projectName ||
            "Sonny Project";

        document
        .getElementById("projectGoal")
        .textContent =
            state.projectGoal ||
            "";

    try {
        const data = await api(
            "/projects/" + state.projectId
        );

        const chat =
            document.getElementById("chat");

        chat.innerHTML = "";

        if (
            data.messages &&
            data.messages.length
        ) {
            data.messages.forEach(
                function(message) {
                    addMessage(
                        message.role === "assistant"
                            ? "sonny"
                            : "user",
                        message.content
                    );
                }
            );
        }
    }
    catch (e) {
        console.error(
            "Could not load conversation history:",
            e
        );
    }

    document
        .getElementById("messageInput")
        .focus();
}  


async function startWorkspace() {

    const button =
        document.getElementById(
            "startButton"
        );

    const error =
        document.getElementById(
            "setupError"
        );

    error.classList.add("hidden");

    const name =
        document
            .getElementById("nameInput")
            .value
            .trim();

    const projectName =
        document
            .getElementById("projectInput")
            .value
            .trim();

    const goal =
        document
            .getElementById("goalInput")
            .value
            .trim();

    const password = document.getElementById("passwordInput").value;

    if (!name || !password) {

        error.textContent =
            "Enter your account ID and password.";

        error.classList.remove(
            "hidden"
        );

        return;
    }

    if (!projectName) {

        error.textContent =
            "Enter a project name.";

        error.classList.remove(
            "hidden"
        );

        return;
    }

    button.disabled = true;
    button.textContent = "Starting...";

    try {

        const loginResult = await api("/auth/login", {
            method: "POST",
            body: JSON.stringify({user_id: name, password: password})
        });
        state.csrfToken = loginResult.csrf_token;
        state.userId = name;
        document.getElementById("passwordInput").value = "";

        const existing = await api("/projects");
        const previous = existing.projects.find(p => p.id === state.projectId);
        const selected = previous || existing.projects[0];
        if (selected) {
            state.projectId = selected.id;
            state.projectName = selected.name;
            state.projectGoal = selected.goal;
        } else {
            const created = await api("/projects", {
                method: "POST",
                body: JSON.stringify({name: projectName, goal: goal})
            });
            state.projectId = created.project_id;
            state.projectName = projectName;
            state.projectGoal = goal;
        }

        saveState();

        showWorkspace();

    }
    catch (e) {

        error.textContent =
            e.message;

        error.classList.remove(
            "hidden"
        );

    }
    finally {

        button.disabled = false;
        button.textContent =
            "Sign in and start Sonny";
    }
}


function addMessage(role, text) {

    const chat =
        document.getElementById("chat");

    const empty =
        document.getElementById(
            "emptyState"
        );

    if (empty) {
        empty.remove();
    }

    const box =
        document.createElement("div");

    box.className =
        "message " + role;

    const label =
        document.createElement("span");

    label.className = "label";

    label.textContent =
        role === "user"
            ? "YOU"
            : "SONNY";

    const content =
        document.createElement("div");

    // Model output is untrusted text. Do not inject it as HTML.
    // Rich Markdown can return after a reviewed sanitizer is installed.
    content.textContent = text;

    box.appendChild(label);
    box.appendChild(content);

    chat.appendChild(box);

    chat.scrollTop =
        chat.scrollHeight;

    return box;
}


async function sendMessage() {

    if (
        !state.userId ||
        !state.projectId
    ) {
        return;
    }

    const input =
        document.getElementById(
            "messageInput"
        );

    const button =
        document.getElementById(
            "sendButton"
        );

    const meta =
        document.getElementById(
            "chatMeta"
        );

    const message =
        input.value.trim();

    if (!message) {
        return;
    }

    input.value = "";

    addMessage(
        "user",
        message
    );

    button.disabled = true;

    meta.textContent =
        "Sonny is thinking...";

    let pending = null;

    try {

        pending =
            addMessage(
                "sonny",
                "Thinking..."
            );

        const result =
            await api(
                "/projects/" +
                encodeURIComponent(
                    state.projectId
                ) +
                "/chat",
                {
                    method: "POST",
                    body: JSON.stringify({
                        message: message
                    })
                }
            );

        if (pending) {
            pending.remove();
        }

        addMessage(
    "sonny",
    result.text ||
    result.response ||
    result.answer ||
    result.message ||
    "Sonny completed the request."
);

        const answerState =
            result.answer_state
                ? " • " +
                  result.answer_state
                : "";

        meta.textContent =
            "Project Co-Pilot" +
            answerState;

    }
    catch (e) {

        if (pending) {
            pending.remove();
        }

        addMessage(
            "sonny",
            "I couldn't complete that request. " +
            e.message
        );

        meta.textContent =
            "Connection error";

    }
    finally {

        button.disabled = false;

        input.focus();
    }
}


function composerKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


async function resetWorkspace() {

    const confirmed =
        confirm(
            "Sign out of Sonny?"
        );

    if (!confirmed) {
        return;
    }

    try { await api("/auth/logout", {method:"POST"}); } catch (_) {}
    localStorage.removeItem("sonny_workspace");

    location.reload();
}


async function checkHealth() {

    try {

        const response =
            await fetch("/health");

        if (!response.ok) {
            throw new Error();
        }

        document
            .getElementById(
                "statusText"
            )
            .textContent =
                "Sonny is online";

    }
    catch (_) {

        document
            .getElementById(
                "statusText"
            )
            .textContent =
                "Connection unavailable";
    }
}


checkHealth();
(async () => {
    try {
        const active = await api("/auth/session");
        state.csrfToken = active.csrf_token;
        state.userId = active.user_id;
        const previous = JSON.parse(localStorage.getItem("sonny_workspace") || "{}");
        const projects = await api("/projects");
        const selected = projects.projects.find(p => p.id === previous.projectId) || projects.projects[0];
        if (selected) {
            state.projectId = selected.id;
            state.projectName = selected.name;
            state.projectGoal = selected.goal;
            saveState();
            await showWorkspace();
        }
    } catch (_) { /* Login required or session expired. */ }
})();

</script>

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
def users_disabled():
    raise HTTPException(403, "Registration is closed")


@app.post("/auth/login")
def login(b: LoginIn, request: Request, response: Response):
    check_origin(request)
    secure = secure_cookie(request)
    client_ip = request.client.host if request.client else "unknown"
    if not login_throttle.allowed_login(b.user_id, client_ip):
        raise HTTPException(429, "Too many login attempts; try again later")
    if not identities.verify_user(b.user_id, b.password):
        login_throttle.failed_login(b.user_id, client_ip)
        raise HTTPException(401, "Invalid credentials")
    login_throttle.succeeded_login(b.user_id)
    # Replace any existing browser session on account switch or re-login.
    sessions.revoke(request.cookies.get("sonny_session"))
    token, csrf = sessions.create(b.user_id)
    response.set_cookie(
        "sonny_session", token, httponly=True, secure=secure,
        samesite="strict", max_age=12 * 60 * 60, path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"csrf_token": csrf}


@app.get("/auth/session")
def session(request: Request, response: Response, u: str = Depends(authenticated_user)):
    csrf = sessions.rotate_csrf(request.cookies.get("sonny_session"))
    response.headers["Cache-Control"] = "no-store"
    return {"authenticated": True, "user_id": u, "csrf_token": csrf}


@app.post("/auth/logout")
def logout(request: Request, response: Response, u: str = Depends(authenticated_user)):
    sessions.revoke(request.cookies.get("sonny_session"))
    response.delete_cookie("sonny_session", path="/", samesite="strict")
    return {"logged_out": True}


# ---------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------

@app.get("/projects")
def list_projects(u: str = Depends(authenticated_user)):
    rows = store.db.execute(
        "SELECT id, name, goal, status FROM projects WHERE user_id=? ORDER BY rowid DESC",
        (u,),
    ).fetchall()
    return {"projects": [dict(row) for row in rows]}



@app.post("/projects")
def projects(
    b: ProjectIn,
    u: str = Depends(authenticated_user)
):
    return {
        "project_id":
            store.create_project(
                u,
                b.name,
                b.goal
            )
    }


@app.get("/projects/{pid}")
def get_project(
    pid: str,
    u: str = Depends(authenticated_user)
):

    p = require_project(u, pid)

    return {
        "project": p,
        "confirmed_memories":
            store.memories(u, pid),
        "actions":
            store.actions(u, pid),
        "messages":
            store.messages(u, pid, limit=50)
    }


# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

@app.post("/projects/{pid}/chat")
def chat(
    pid: str,
    b: ChatIn,
    u: str = Depends(authenticated_user)
):
    u = u

    p = require_project(u, pid)

    t = time.time()

    # Persist the user's turn first.
    store.add_message(
        u,
        pid,
        "user",
        b.message
    )

    # Load a bounded recent-history window.
    # The current user message is included here.
    history = store.messages(
        u,
        pid,
        limit=20
    )

    out = respond(
        p,
        store.memories(u, pid),
        b.message,
        history=history
    )

    rid = str(uuid.uuid4())

    # Persist Sonny's response as part of the
    # same durable project conversation.
    store.add_message(
        u,
        pid,
        "assistant",
        out["text"],
        response_id=rid
    )

    latency = int(
        (time.time() - t) * 1000
    )

    store.trace(
        rid,
        u,
        pid,
        "openai-responses",
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
    u: str = Depends(authenticated_user)
):

    u = u

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
    u: str = Depends(authenticated_user)
):

    u = u

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
    u: str = Depends(authenticated_user)
):

    u = u

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
    u: str = Depends(authenticated_user)
):

    u = u

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
    u: str = Depends(authenticated_user)
):

    u = u

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
    u: str = Depends(authenticated_user)
):

    u = u

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
