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


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN VULNERABILITY: X-User-ID alone impersonates an account",
)
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
    assert response.status_code in (401, 403)
