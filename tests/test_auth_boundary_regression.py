"""Authentication boundary regression tests.

Verify that forged identity headers, expired sessions, and cross-account
access are rejected. Tests must pass before deployment.
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


def test_signed_session_cannot_access_other_users_project(client):
    import jwt
    import time
    http, store = client
    owner = store.create_user("owner")
    intruder = store.create_user("intruder")
    project = store.create_project(owner, "private", "goal")
    now = int(time.time())
    token = jwt.encode(
        {"sub": intruder, "iat": now, "exp": now + 3600},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.get(
        f"/projects/{project}",
        headers={"Authorization": f"Bearer {token}", "X-User-ID": intruder},
    )
    assert response.status_code == 404


def test_mismatched_header_and_signed_identity_rejected(client):
    import jwt
    import time
    http, store = client
    owner = store.create_user("owner")
    intruder = store.create_user("intruder")
    project = store.create_project(owner, "private", "goal")
    now = int(time.time())
    token = jwt.encode(
        {"sub": intruder, "iat": now, "exp": now + 3600},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.get(
        f"/projects/{project}",
        headers={"Authorization": f"Bearer {token}", "X-User-ID": owner},
    )
    assert response.status_code == 403


def test_registration_issues_working_session(client):
    http, _ = client
    created = http.post("/users", json={"name": "test account"})
    assert created.status_code == 200
    payload = created.json()
    assert payload["session_token"]
    project = http.post(
        "/projects",
        json={"name": "new project", "goal": "test"},
        headers={
            "Authorization": f"Bearer {payload['session_token']}",
            "X-User-ID": payload["user_id"],
        },
    )
    assert project.status_code == 200


def test_invalid_signature_rejected(client):
    import jwt
    import time
    http, store = client
    owner = store.create_user("owner")
    project = store.create_project(owner, "private", "goal")
    now = int(time.time())
    forged = jwt.encode(
        {"sub": owner, "iat": now, "exp": now + 3600},
        "wrong-signing-key", algorithm="HS256",
    )
    response = http.get(
        f"/projects/{project}",
        headers={"Authorization": f"Bearer {forged}", "X-User-ID": owner},
    )
    assert response.status_code == 401


def test_chat_rejects_unauthenticated_requests(client):
    http, store = client
    owner = store.create_user("owner")
    project = store.create_project(owner, "private", "goal")
    response = http.post(
        f"/projects/{project}/chat",
        headers={"X-User-ID": owner},
        json={"message": "should never reach model"},
    )
    assert response.status_code == 401
    assert store.messages(owner, project) == []


def test_memory_mutation_rejects_unauthenticated_requests(client):
    http, store = client
    owner = store.create_user("owner")
    project = store.create_project(owner, "private", "goal")
    response = http.post(
        f"/projects/{project}/memories",
        headers={"X-User-ID": owner},
        json={"value": "unauthorized", "type": "fact"},
    )
    assert response.status_code == 401
    assert store.memories(owner, project) == []


def test_other_user_cannot_write_to_private_project(client):
    import jwt
    import time
    http, store = client
    owner = store.create_user("owner")
    intruder = store.create_user("intruder")
    project = store.create_project(owner, "private", "goal")
    now = int(time.time())
    token = jwt.encode(
        {"sub": intruder, "iat": now, "exp": now + 3600},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.post(
        f"/projects/{project}/memories",
        headers={"Authorization": f"Bearer {token}", "X-User-ID": intruder},
        json={"value": "unauthorized", "type": "fact"},
    )
    assert response.status_code == 404
    assert store.memories(owner, project) == []


def test_signed_token_for_nonexistent_account_rejected(client):
    import jwt
    import time
    http, _ = client
    now = int(time.time())
    token = jwt.encode(
        {"sub": "deleted-or-nonexistent-user", "iat": now, "exp": now + 3600},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.post(
        "/projects",
        json={"name": "should not exist", "goal": "test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_registration_fails_closed_without_signing_secret(client, monkeypatch):
    http, _ = client
    monkeypatch.delenv("SONNY_AUTH_SECRET", raising=False)
    response = http.post("/users", json={"name": "test"})
    assert response.status_code == 503


def test_registration_fails_closed_with_short_signing_secret(client, monkeypatch):
    http, _ = client
    monkeypatch.setenv("SONNY_AUTH_SECRET", "too-short")
    response = http.post("/users", json={"name": "test"})
    assert response.status_code == 503


def test_existing_session_rejected_if_signing_key_removed(client, monkeypatch):
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
    monkeypatch.delenv("SONNY_AUTH_SECRET", raising=False)
    response = http.get(
        f"/projects/{project}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503


def test_renewal_requires_existing_session(client):
    http, store = client
    owner = store.create_user("owner")
    response = http.post("/session/renew", headers={"X-User-ID": owner})
    assert response.status_code == 401


def test_renewal_returns_signed_token_for_same_account(client):
    import jwt
    import time
    http, store = client
    owner = store.create_user("owner")
    now = int(time.time())
    original = jwt.encode(
        {"sub": owner, "iat": now, "exp": now + 3600},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.post(
        "/session/renew",
        headers={"Authorization": f"Bearer {original}", "X-User-ID": owner},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == owner
    claims = jwt.decode(
        payload["session_token"],
        "test-only-signing-key-not-for-production", algorithms=["HS256"],
    )
    assert claims["sub"] == owner
    assert claims["exp"] > now + 3600


def test_expired_session_cannot_be_renewed(client):
    import jwt
    http, store = client
    owner = store.create_user("owner")
    expired = jwt.encode(
        {"sub": owner, "iat": 1, "exp": 2},
        "test-only-signing-key-not-for-production", algorithm="HS256",
    )
    response = http.post(
        "/session/renew",
        headers={"Authorization": f"Bearer {expired}", "X-User-ID": owner},
    )
    assert response.status_code == 401


def test_private_project_response_is_not_cacheable(client):
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
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"


def test_registration_token_response_is_not_cacheable(client):
    http, _ = client
    response = http.post("/users", json={"name": "test"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
