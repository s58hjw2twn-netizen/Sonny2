"""Database-backed opaque sessions for AUTH-002.

Tokens are never stored in plaintext. Callers must set secure cookie flags,
check CSRF for unsafe methods, and avoid logging credentials.
"""
import hashlib
import secrets
import time


SESSION_SECONDS = 60 * 60 * 12


class SessionStore:
    def __init__(self, db):
        self.db = db

    def initialize(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                csrf_hash TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                revoked_at INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        self.db.commit()

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def create(self, user_id):
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        expiry = int(time.time()) + SESSION_SECONDS
        self.db.execute(
            "INSERT INTO auth_sessions(token_hash,user_id,csrf_hash,expires_at) "
            "VALUES(?,?,?,?)",
            (self.digest(token), user_id, self.digest(csrf), expiry),
        )
        self.db.commit()
        return token, csrf

    def resolve(self, token):
        if not token:
            return None
        row = self.db.execute(
            "SELECT user_id FROM auth_sessions WHERE token_hash=? "
            "AND revoked_at IS NULL AND expires_at>?",
            (self.digest(token), int(time.time())),
        ).fetchone()
        return row[0] if row else None

    def valid_csrf(self, token, csrf):
        if not token or not csrf:
            return False
        row = self.db.execute(
            "SELECT 1 FROM auth_sessions WHERE token_hash=? AND csrf_hash=? "
            "AND revoked_at IS NULL AND expires_at>?",
            (self.digest(token), self.digest(csrf), int(time.time())),
        ).fetchone()
        return row is not None

    def revoke(self, token):
        if token:
            self.db.execute(
                "UPDATE auth_sessions SET revoked_at=? WHERE token_hash=?",
                (int(time.time()), self.digest(token)),
            )
            self.db.commit()

    def rotate_csrf(self, token):
        """Rotate CSRF proof when restoring an authenticated browser session."""
        if not self.resolve(token):
            return None
        csrf = secrets.token_urlsafe(32)
        self.db.execute(
            "UPDATE auth_sessions SET csrf_hash=? WHERE token_hash=? "
            "AND revoked_at IS NULL AND expires_at>?",
            (self.digest(csrf), self.digest(token), int(time.time())),
        )
        self.db.commit()
        return csrf
