"""AUTH-001 isolated persistence tests; no API routes changed."""
import sqlite3

import pytest

from sonny.identity_store import IdentityStore


@pytest.fixture
def identity(tmp_path):
    db = sqlite3.connect(tmp_path / "identity.db")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE users(id TEXT PRIMARY KEY, name TEXT NOT NULL)")
    db.execute("INSERT INTO users VALUES('owner-1', 'Owner')")
    db.execute("INSERT INTO users VALUES('other-2', 'Other')")
    db.execute("CREATE TABLE projects(id TEXT PRIMARY KEY, user_id TEXT NOT NULL)")
    db.execute("INSERT INTO projects VALUES('project-1', 'owner-1')")
    db.commit()
    store = IdentityStore(db)
    store.initialize()
    yield store, db
    db.close()


def test_existing_owner_can_enroll_and_verify(identity):
    store, db = identity
    store.enroll_existing_owner("owner-1", "long private passphrase")
    assert store.verify_owner("owner-1", "long private passphrase")
    assert not store.verify_owner("owner-1", "wrong")
    assert db.execute("SELECT user_id FROM projects").fetchone()[0] == "owner-1"


def test_unknown_user_cannot_enroll(identity):
    store, db = identity
    with pytest.raises(ValueError, match="not found"):
        store.enroll_existing_owner("nonexistent", "long private passphrase")
    assert db.execute("SELECT COUNT(*) FROM auth_credentials").fetchone()[0] == 0


def test_second_owner_enrollment_is_blocked(identity):
    store, db = identity
    store.enroll_existing_owner("owner-1", "first private passphrase")
    with pytest.raises(ValueError, match="already enrolled"):
        store.enroll_existing_owner("other-2", "second private passphrase")
    assert not store.verify_owner("other-2", "second private passphrase")


def test_no_plaintext_password_stored(identity):
    store, db = identity
    store.enroll_existing_owner("owner-1", "distinctive secret phrase")
    stored = db.execute(
        "SELECT password_verifier FROM auth_credentials"
    ).fetchone()[0]
    assert "distinctive secret phrase" not in stored
    assert stored.startswith("scrypt$")


def test_reinitialization_preserves_credentials(identity):
    store, db = identity
    store.enroll_existing_owner("owner-1", "long private passphrase")
    IdentityStore(db).initialize()
    assert store.verify_owner("owner-1", "long private passphrase")
