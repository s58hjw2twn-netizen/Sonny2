"""AUTH-003 tests. Run in isolated test process with a fresh database."""
import os
import tempfile

fd, path = tempfile.mkstemp()
os.close(fd)
os.environ["SONNY_DB"] = path
os.environ["SONNY_ALLOW_HTTP_LOCAL"] = "1"

from fastapi.testclient import TestClient
from sonny.app import app, store, identities

def test_project_recovery_and_cross_user_listing():
    owner = store.create_user("Owner")
    other = store.create_user("Other")
    identities.enroll_existing_user(owner, "owner secret phrase")
    identities.enroll_existing_user(other, "other secret phrase")
    a = TestClient(app)
    b = TestClient(app)
    csrf_a = a.post("/auth/login", json={"user_id": owner, "password": "owner secret phrase"}).json()["csrf_token"]
    created = a.post("/projects", headers={"X-CSRF-Token": csrf_a},
                     json={"name": "Preserved", "goal": "Keep data"})
    assert created.status_code == 200
    pid = created.json()["project_id"]
    assert [p["id"] for p in a.get("/projects").json()["projects"]] == [pid]
    assert b.post("/auth/login", json={"user_id": other, "password": "other secret phrase"}).status_code == 200
    assert b.get("/projects").json()["projects"] == []
    assert b.get("/projects/" + pid, headers={"X-User-ID": owner}).status_code == 404
    restored = a.get("/auth/session")
    assert restored.status_code == 200
    new_csrf = restored.json()["csrf_token"]
    assert new_csrf != csrf_a
    assert a.post("/projects", headers={"X-CSRF-Token": csrf_a},
                  json={"name": "No", "goal": "Old token"}).status_code == 403
    assert a.post("/projects", headers={"X-CSRF-Token": new_csrf},
                  json={"name": "Yes", "goal": "New token"}).status_code == 200


def test_failed_login_throttles_account():
    uid = store.create_user("Throttle")
    identities.enroll_existing_user(uid, "correct private passphrase")
    c = TestClient(app)
    for _ in range(5):
        assert c.post("/auth/login", json={"user_id": uid, "password": "wrong"}).status_code == 401
    assert c.post("/auth/login", json={"user_id": uid, "password": "correct private passphrase"}).status_code == 429


def test_cross_origin_login_is_rejected():
    uid = store.create_user("Origin")
    identities.enroll_existing_user(uid, "origin private passphrase")
    c = TestClient(app)
    response = c.post(
        "/auth/login",
        headers={"Origin": "https://untrusted.example"},
        json={"user_id": uid, "password": "origin private passphrase"},
    )
    assert response.status_code == 403
    assert "sonny_session" not in c.cookies


def test_session_expiry_and_revocation():
    from sonny.app import sessions
    from unittest.mock import patch
    uid = store.create_user("Expiry")
    token, csrf = sessions.create(uid)
    assert sessions.resolve(token) == uid
    assert sessions.valid_csrf(token, csrf)
    with patch("sonny.sessions.time.time", return_value=10**12):
        assert sessions.resolve(token) is None
        assert not sessions.valid_csrf(token, csrf)
    sessions.revoke(token)
    assert sessions.resolve(token) is None


def test_ip_throttle_blocks_password_spraying():
    from sonny.login_throttle import LoginThrottle
    import sqlite3
    db = sqlite3.connect(":memory:")
    throttle = LoginThrottle(db)
    throttle.initialize()
    ip = "198.51.100.9"
    for i in range(5):
        assert throttle.allowed_login("account-" + str(i), ip)
        throttle.failed_login("account-" + str(i), ip)
    assert not throttle.allowed_login("new-account", ip)
    assert throttle.allowed_login("new-account", "198.51.100.10")
    # A spoofable X-Forwarded-For header is not used as the identity source.
