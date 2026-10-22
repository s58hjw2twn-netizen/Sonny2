"""Private owner build smoke tests; no external model calls."""
import os
import tempfile

fd, path = tempfile.mkstemp(prefix="sonny-smoke-", suffix=".db")
os.close(fd)
os.unlink(path)
os.environ["SONNY_DB"] = path
os.environ["SONNY_ALLOW_HTTP_LOCAL"] = "1"

from fastapi.testclient import TestClient
from sonny.app import app, store, identities


def test_mobile_page_and_safe_reply_rendering():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert 'name="viewport"' in html
        assert "async function startWorkspace()" in html
        assert 'content.textContent = text;' in html
        assert 'content.innerHTML = renderMarkdown(text);' not in html


def test_owner_login_project_memory_and_reload():
    owner = store.create_user("Private owner smoke")
    identities.enroll_existing_user(owner, "private-owner-test-passphrase")
    with TestClient(app) as client:
        login = client.post("/auth/login", json={
            "user_id": owner, "password": "private-owner-test-passphrase"
        })
        assert login.status_code == 200
        csrf = login.json()["csrf_token"]
        created = client.post("/projects", headers={"X-CSRF-Token": csrf},
                              json={"name": "iPhone test", "goal": "Keep progress"})
        assert created.status_code == 200
        pid = created.json()["project_id"]
        memory = client.post(f"/projects/{pid}/memories",
                             headers={"X-CSRF-Token": csrf},
                             json={"value": "Private owner memory"})
        assert memory.status_code == 200
        mid = memory.json()["memory_id"]
        confirmed = client.post(f"/projects/{pid}/memories/{mid}/confirm",
                                headers={"X-CSRF-Token": csrf})
        assert confirmed.status_code == 200

        # Simulates reopening Safari while the persistent cookie remains.
        resumed = client.get("/auth/session")
        assert resumed.status_code == 200
        assert resumed.json()["csrf_token"] != csrf
        listing = client.get("/projects")
        assert listing.status_code == 200
        assert any(p["id"] == pid for p in listing.json()["projects"])
        project = client.get(f"/projects/{pid}")
        assert project.status_code == 200
        assert [m["value"] for m in project.json()["confirmed_memories"]] == [
            "Private owner memory"
        ]
        logout = client.post("/auth/logout", headers={
            "X-CSRF-Token": resumed.json()["csrf_token"]
        })
        assert logout.status_code == 200
        assert client.get(f"/projects/{pid}").status_code == 401
