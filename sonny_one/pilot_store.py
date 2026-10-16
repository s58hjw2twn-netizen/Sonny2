"""SQLite persistence for the local test-account pilot, separate from research."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
import uuid

DEFAULT_GOAL = 'Build a useful personal assistant'


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384,
                            r=8, p=1, dklen=32, maxmem=64 * 1024 * 1024)
    return f'scrypt${salt}${digest.hex()}'


def verify_password(password, encoded):
    _, salt, expected = encoded.split('$')
    actual = password_hash(password, salt).split('$')[2]
    return hmac.compare_digest(actual, expected)


class PilotStore:
    def __init__(self, path):
        self.path = str(path)
        if self.path == ':memory:':
            raise ValueError('Use a file database; each operation has its own connection')
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        except FileExistsError:
            pass
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS accounts(
              id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(
              id_hash TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES accounts(id), expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS workspaces(
              owner TEXT PRIMARY KEY REFERENCES accounts(id), goal TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS facts(
              id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES accounts(id), statement TEXT NOT NULL,
              source TEXT NOT NULL, approved_at TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS fact_events(
              id INTEGER PRIMARY KEY, owner TEXT NOT NULL, fact_id TEXT NOT NULL,
              event TEXT NOT NULL, happened_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS messages(
              id INTEGER PRIMARY KEY, owner TEXT NOT NULL REFERENCES accounts(id), role TEXT NOT NULL,
              text TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS turns(
              id INTEGER PRIMARY KEY, owner TEXT NOT NULL REFERENCES accounts(id), request_id TEXT NOT NULL,
              message TEXT NOT NULL, response TEXT NOT NULL, UNIQUE(owner,request_id));
            CREATE INDEX IF NOT EXISTS facts_owner ON facts(owner);
            CREATE INDEX IF NOT EXISTS messages_owner ON messages(owner,id);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA secure_delete=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_user(self, username, password):
        import re
        if not re.fullmatch(r'[a-z0-9_.-]{3,64}', username):
            raise ValueError('Username must contain 3–64 lowercase letters, digits, dots, underscores or hyphens')
        if not 12 <= len(password) <= 128:
            raise ValueError('Test-account passwords must contain 12–128 characters')
        owner = str(uuid.uuid4())
        encoded = password_hash(password)
        with self.connect() as db:
            db.execute('INSERT INTO accounts VALUES(?,?,?)', (owner, username, encoded))
            db.execute('INSERT INTO workspaces(owner,goal) VALUES(?,?)', (owner, DEFAULT_GOAL))
        return owner

    def account(self, username):
        with self.connect() as db:
            row = db.execute('SELECT * FROM accounts WHERE username=?', (username,)).fetchone()
            return dict(row) if row else None

    def add_session(self, owner, sid, expires):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE expires<=?', (time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (self.session_hash(sid), owner, expires))

    @staticmethod
    def session_hash(sid):
        return hashlib.sha256(sid.encode()).hexdigest()

    def session_valid(self, owner, sid):
        with self.connect() as db:
            return db.execute('SELECT 1 FROM sessions WHERE id_hash=? AND owner=? AND expires>?',
                              (self.session_hash(sid), owner, time.time())).fetchone() is not None

    def revoke_session(self, sid):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE id_hash=?', (self.session_hash(sid),))

    def workspace(self, owner):
        with self.connect() as db:
            db.execute('BEGIN')
            return self._workspace(db, owner)

    @staticmethod
    def _workspace(db, owner):
        workspace = dict(db.execute('SELECT goal,version FROM workspaces WHERE owner=?', (owner,)).fetchone())
        workspace['memories'] = [dict(row) for row in db.execute(
            'SELECT id,statement,source,approved_at,revision FROM facts WHERE owner=? ORDER BY rowid', (owner,))]
        workspace['messages'] = [dict(row) for row in db.execute(
            'SELECT role,text FROM messages WHERE owner=? ORDER BY id', (owner,))]
        return workspace

    def set_goal(self, owner, goal):
        with self.connect() as db:
            db.execute('UPDATE workspaces SET goal=?,version=version+1 WHERE owner=?', (goal, owner))

    def save_fact(self, owner, statement):
        fact_id = str(uuid.uuid4())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM facts WHERE owner=?', (owner,)).fetchone()[0] >= 50:
                raise ValueError('Memory is full; forget a fact before saving another')
            db.execute('INSERT INTO facts(id,owner,statement,source,approved_at) VALUES(?,?,?,?,?)',
                       (fact_id, owner, statement, 'explicit_user_statement', timestamp()))
            db.execute('INSERT INTO fact_events(owner,fact_id,event,happened_at) VALUES(?,?,?,?)',
                       (owner, fact_id, 'APPROVED', timestamp()))
            db.execute('UPDATE workspaces SET version=version+1 WHERE owner=?', (owner,))
        return fact_id

    def correct_fact(self, owner, fact_id, statement, revision):
        with self.connect() as db:
            row = db.execute('SELECT revision FROM facts WHERE id=? AND owner=?', (fact_id, owner)).fetchone()
            if row is None:
                return 'missing'
            changed = db.execute('UPDATE facts SET statement=?,revision=revision+1,approved_at=? '
                                 'WHERE id=? AND owner=? AND revision=?',
                                 (statement, timestamp(), fact_id, owner, revision)).rowcount
            if not changed:
                return 'conflict'
            db.execute('INSERT INTO fact_events(owner,fact_id,event,happened_at) VALUES(?,?,?,?)',
                       (owner, fact_id, 'CORRECTED', timestamp()))
            db.execute('DELETE FROM turns WHERE owner=?', (owner,))
            db.execute('UPDATE workspaces SET version=version+1 WHERE owner=?', (owner,))
            return 'corrected'

    def forget_fact(self, owner, fact_id):
        with self.connect() as db:
            changed = db.execute('DELETE FROM facts WHERE id=? AND owner=?', (fact_id, owner)).rowcount
            if changed:
                db.execute('DELETE FROM fact_events WHERE fact_id=? AND owner=?', (fact_id, owner))
                db.execute('DELETE FROM turns WHERE owner=?', (owner,))
                db.execute('UPDATE workspaces SET version=version+1 WHERE owner=?', (owner,))
            return bool(changed)

    def clear_chat(self, owner):
        with self.connect() as db:
            db.execute('DELETE FROM messages WHERE owner=?', (owner,))
            db.execute('DELETE FROM turns WHERE owner=?', (owner,))
            db.execute('UPDATE workspaces SET version=version+1 WHERE owner=?', (owner,))

    def erase(self, owner):
        with self.connect() as db:
            for table in ('facts', 'fact_events', 'messages', 'turns'):
                db.execute(f'DELETE FROM {table} WHERE owner=?', (owner,))
            db.execute('UPDATE workspaces SET goal=?,version=version+1 WHERE owner=?', (DEFAULT_GOAL, owner))

    def reply(self, owner, message, request_id, responder):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT message,response FROM turns WHERE owner=? AND request_id=?',
                                  (owner, request_id)).fetchone()
            if previous:
                if previous['message'] != message:
                    raise ValueError('Request identifier already used for a different message')
                return json.loads(previous['response'])
            workspace = self._workspace(db, owner)
            out = responder(message, workspace['goal'], [m['statement'] for m in workspace['memories']])
            for role, text in (('user', message), ('assistant', out['text'])):
                db.execute('INSERT INTO messages(owner,role,text,created_at) VALUES(?,?,?,?)',
                           (owner, role, text, timestamp()))
            db.execute('DELETE FROM messages WHERE owner=? AND id NOT IN '
                       '(SELECT id FROM messages WHERE owner=? ORDER BY id DESC LIMIT 100)', (owner, owner))
            db.execute('UPDATE workspaces SET version=version+1 WHERE owner=?', (owner,))
            db.execute('INSERT INTO turns(owner,request_id,message,response) VALUES(?,?,?,?)',
                       (owner, request_id, message, json.dumps(out)))
            db.execute('DELETE FROM turns WHERE owner=? AND id NOT IN '
                       '(SELECT id FROM turns WHERE owner=? ORDER BY id DESC LIMIT 100)', (owner, owner))
            return out
