"""AUTH-001 multi-account credential persistence; not yet wired to API routes.

Enrollment is an internal operation. Public registration remains disabled until
email verification, rate limiting, and abuse controls are implemented.
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

    def enroll_existing_user(self, user_id: str, password: str) -> None:
        """Bind an existing user to a credential exactly once.

        Caller must independently verify ownership before migration.
        This is not a public registration endpoint.
        """
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("An existing user ID is required")
        verifier = hash_password(password)
        try:
            self.db.execute("BEGIN IMMEDIATE")
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

    def verify_user(self, user_id: str, password: str) -> bool:
        """Credential check only; not a session or authentication endpoint."""
        if not isinstance(user_id, str) or not isinstance(password, str):
            return False
        row = self.db.execute(
            "SELECT password_verifier FROM auth_credentials WHERE user_id=?",
            (user_id,)
        ).fetchone()
        return bool(row and verify_password(password, row[0]))
