"""AUTH-001 credential storage; not wired into public API routes.

Enrollment must only be invoked from a trusted local/admin bootstrap path
after independently verifying the intended existing user ID.
"""
import sqlite3

from .credentials import hash_password, verify_password


class IdentityStore:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection

    def initialize(self):
        """Additive schema; leaves existing users and projects unchanged."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS auth_credentials (
                user_id TEXT PRIMARY KEY,
                password_verifier TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        self.db.commit()

    def enroll_existing_owner(self, user_id: str, password: str) -> None:
        """Bind one pre-existing user to a credential, once only.

        This is deliberately NOT a public signup API. Caller must verify
        ownership and make a backup before invoking it.
        """
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("An existing user ID is required")
        verifier = hash_password(password)
        try:
            self.db.execute("BEGIN IMMEDIATE")
            count = self.db.execute(
                "SELECT COUNT(*) FROM auth_credentials"
            ).fetchone()[0]
            if count:
                raise ValueError("Owner already enrolled")
            existing = self.db.execute(
                "SELECT 1 FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if existing is None:
                raise ValueError("User ID not found")
            self.db.execute(
                "INSERT INTO auth_credentials(user_id, password_verifier) "
                "VALUES(?, ?)", (user_id, verifier)
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def verify_owner(self, user_id: str, password: str) -> bool:
        """Credential check only; not a session or authentication endpoint."""
        if not isinstance(user_id, str) or not isinstance(password, str):
            return False
        row = self.db.execute(
            "SELECT password_verifier FROM auth_credentials WHERE user_id=?",
            (user_id,)
        ).fetchone()
        return bool(row and verify_password(password, row[0]))
