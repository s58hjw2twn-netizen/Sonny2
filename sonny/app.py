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
            Start your Sonny workspace
        </div>

        <div class="row">

            <input
                id="nameInput"
                placeholder="Your name"
                autocomplete="name"
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
                Start Sonny
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
                New
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
    projectId: null,
    projectName: null,
    projectGoal: null
};


function apiHeaders() {

    const h = {
        "Content-Type": "application/json"
    };

    if (state.userId) {
        h["X-User-ID"] = state.userId;
    }

    return h;
}


async function api(path, options = {}) {

    const response = await fetch(
        path,
        {
            ...options,
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
        JSON.stringify(state)
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
            saved.userId &&
            saved.projectId
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


function showWorkspace() {

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

    if (!name) {

        error.textContent =
            "Enter your name.";

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

        const createdUser =
            await api(
                "/users",
                {
                    method: "POST",
                    body: JSON.stringify({
                        name: name
                    })
                }
            );

        state.userId =
            createdUser.user_id;

        const createdProject =
            await api(
                "/projects",
                {
                    method: "POST",
                    body: JSON.stringify({
                        name: projectName,
                        goal: goal
                    })
                }
            );

        state.projectId =
            createdProject.project_id;

        state.projectName =
            projectName;

        state.projectGoal =
            goal;

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
            "Start Sonny";
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

    if (role === "sonny") {
    content.innerHTML = renderMarkdown(text);
}
else {
    content.textContent = text;
}

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


function resetWorkspace() {

    const confirmed =
        confirm(
            "Start a new Sonny workspace?"
        );

    if (!confirmed) {
        return;
    }

    localStorage.removeItem(
        "sonny_workspace"
    );

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
loadState();

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
    x_user_id: str | None = Header(None)
):

    u = user(x_user_id)

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
