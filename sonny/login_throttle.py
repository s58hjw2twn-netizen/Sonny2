"""Persistent per-account login throttling (additional IP throttling required for production)."""
import hashlib
import time


class LoginThrottle:
    WINDOW = 15 * 60
    MAX_FAILURES = 5

    def __init__(self, db):
        self.db = db

    def initialize(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS auth_login_attempts (
                account_hash TEXT PRIMARY KEY,
                failures INTEGER NOT NULL,
                window_started INTEGER NOT NULL
            )
        """)
        self.db.commit()

    @staticmethod
    def key(user_id):
        return hashlib.sha256(user_id.encode("utf-8")).hexdigest()

    def allowed(self, user_id):
        now = int(time.time())
        row = self.db.execute(
            "SELECT failures,window_started FROM auth_login_attempts WHERE account_hash=?",
            (self.key(user_id),),
        ).fetchone()
        return not row or now - row[1] >= self.WINDOW or row[0] < self.MAX_FAILURES

    def failed(self, user_id):
        now = int(time.time())
        key = self.key(user_id)
        self.db.execute("""
            INSERT INTO auth_login_attempts(account_hash,failures,window_started)
            VALUES(?,1,?)
            ON CONFLICT(account_hash) DO UPDATE SET
                failures=CASE WHEN ?-window_started>=? THEN 1 ELSE failures+1 END,
                window_started=CASE WHEN ?-window_started>=? THEN ? ELSE window_started END
        """, (key, now, now, self.WINDOW, now, self.WINDOW, now))
        self.db.commit()

    def succeeded(self, user_id):
        self.db.execute("DELETE FROM auth_login_attempts WHERE account_hash=?",
                        (self.key(user_id),))
        self.db.commit()
