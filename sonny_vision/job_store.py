"""Persistent approval state, owned by the server rather than customer requests.

SQLite is appropriate for a single-process prototype. Production deployment
requires transaction discipline, backups, authenticated application endpoints,
and a migration strategy. No clean master is delivered by this module.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path


def initialize_jobs(database_path: str) -> None:
    with sqlite3.connect(database_path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS vision_jobs (
            job_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            proof_sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN (
                'awaiting_customer_approval',
                'approved_pending_release_checks',
                'revision_requested')),
            CHECK (length(job_id) > 0 AND length(customer_id) > 0
                   AND length(proof_sha256) = 64)
        )""")


def create_job(database_path: str, job_id: str, customer_id: str,
               proof_sha256: str) -> None:
    if not job_id or not customer_id or len(proof_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in proof_sha256):
        raise ValueError("Invalid job identifiers or proof hash")
    with sqlite3.connect(database_path) as db:
        db.execute("INSERT INTO vision_jobs VALUES (?, ?, ?, ?)",
                   (job_id, customer_id, proof_sha256,
                    "awaiting_customer_approval"))


def get_customer_job(database_path: str, job_id: str,
                     authenticated_customer_id: str) -> tuple[str, str] | None:
    if not authenticated_customer_id:
        return None
    with sqlite3.connect(database_path) as db:
        row = db.execute(
            "SELECT status, proof_sha256 FROM vision_jobs "
            "WHERE job_id = ? AND customer_id = ?",
            (job_id, authenticated_customer_id)).fetchone()
    return tuple(row) if row else None


def record_customer_decision(database_path: str, job_id: str,
                             authenticated_customer_id: str,
                             approved: bool) -> bool:
    if not authenticated_customer_id or type(approved) is not bool:
        return False
    new_status = ("approved_pending_release_checks"
                  if approved else "revision_requested")
    with sqlite3.connect(database_path) as db:
        result = db.execute(
            "UPDATE vision_jobs SET status = ? WHERE job_id = ? "
            "AND customer_id = ? AND status = 'awaiting_customer_approval'",
            (new_status, job_id, authenticated_customer_id))
        return result.rowcount == 1
