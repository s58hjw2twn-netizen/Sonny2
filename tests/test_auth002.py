"""AUTH-002 tests for session isolation and CSRF.

Run in a fresh process with SONNY_DB pointing to an isolated test database.
"""
import os
import tempfile

fd, path = tempfile.mkstemp()
os.close(fd)
os.environ["SONNY_DB"] = path
os.environ["SONNY_ALLOW_HTTP_LOCAL"] = "1"

from fastapi.testclient import TestClient
from sonny.app import app, store, identities

client = TestClient(app)


def login_as(uid, password):
    response = client.post("/auth/login", json={"user_id": uid, "password": password})
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_protected_routes_reject_anonymous_and_header_impersonation():
    user_id = store.create_user("First")
    assert client.post("/projects", headers={"X-User-ID": user_id},
                       json={"name": "Secret", "goal": "Private"}).status_code == 401
    assert client.post("/users", json={"name": "Anonymous"}).status_code == 403


def test_login_csrf_and_logout():
    uid = store.create_user("Owner")
    identities.enroll_existing_user(uid, "private passphrase")
    assert client.post("/auth/login", json={"user_id": uid, "password": "wrong"}).status_code == 401
    csrf = login_as(uid, "private passphrase")
    assert client.post("/projects", json={"name": "A", "goal": "B"}).status_code == 403
    created = client.post("/projects", headers={"X-CSRF-Token": csrf},
                          json={"name": "A", "goal": "B"})
    assert created.status_code == 200
    assert client.post("/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/projects/" + created.json()["project_id"]).status_code == 401


def test_cross_user_identity_cannot_be_overridden():
    first = store.create_user("A")
    second = store.create_user("B")
    identities.enroll_existing_user(first, "first passphrase")
    identities.enroll_existing_user(second, "second passphrase")
    csrf = login_as(first, "first passphrase")
    p = client.post("/projects", headers={"X-CSRF-Token": csrf},
                    json={"name": "Private", "goal": "Secret"}).json()["project_id"]
    login_as(second, "second passphrase")
    assert client.get("/projects/" + p, headers={"X-User-ID": first}).status_code == 404
