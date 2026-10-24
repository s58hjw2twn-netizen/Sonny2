"""Authentication boundary regression tests.

The known vulnerability is deliberately tracked as an expected failure until
verified authentication replaces the untrusted X-User-ID header. Never turn
this xfail into a skip or remove it to make CI green.
"""
import pytest
from fastapi.testclient import TestClient

from sonny import app as app_module
from sonny.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SONNY_AUTH_SECRET", "test-only-signing-key-not-for-production")
    store = Store(str(tmp_path / "auth-boundary.sqlite3"))
    monkeypatch.setattr(app_module, "store", store)
    with TestClient(app_module.app) as test_client:
        yield test_client, store
    store.db.close()


def test_project_requires_identity_header(client):
    http, store = client
    victim = store.create_user("victim")
    project = store.create_project(victim, "private", "confidential")
    response = http.get(f"/projects/{project}")
    assert response.status_code == 401


def test_untrusted_header_cannot_impersonate_user(client):
    http, store = client
    victim = store.create_user("victim")
    project = store.create_project(victim, "private", "confidential")
    store.add_message(victim, project, "user", "private conversation")
    # Attacker possesses an identifier but no authenticated session.
    response = http.get(
        f"/projects/{project}",
        headers={"X-User-ID": victim},
    )
    assert response.status_code == 401


def test_valid_signed_session_allows_own_project(client):
    import jwt
    import time
    http, store = client
    owner = store.create_user("owner")
    project = store.create_project(owner, "private", "goal")
    now = int(time.time())
    token = jwt.encode(
        {"sub": owner, "iat": now, "exp": now + 3600},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.get(
        f"/projects/{project}",
        headers={"Authorization": f"Bearer {token}", "X-User-ID": owner},
    )
    assert response.status_code == 200


def test_expired_session_rejected(client):
    import jwt
    http, store = client
    owner = store.create_user("owner")
    project = store.create_project(owner, "private", "goal")
    token = jwt.encode(
        {"sub": owner, "iat": 1, "exp": 2},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.get(
        f"/projects/{project}",
        headers={"Authorization": f"Bearer {token}", "X-User-ID": owner},
    )
    assert response.status_code == 401
