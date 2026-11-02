"""Durable, atomic replay reservation for trusted speech orchestration.

This store only reserves identifiers; it does not authenticate consent or run
speech models. The trusted host must own the database path and its permissions.
"""
import sqlite3
from pathlib import Path
from .voice_speech_execution_authorization import (
    SpeechExecutionAuthorization, validate_speech_authorization,
)

def reserve_speech_run(database: Path, request: SpeechExecutionAuthorization) -> bool:
    if not validate_speech_authorization(request):
        return False
    if not isinstance(database, Path) or database.is_symlink():
        raise ValueError("trusted database path required")
    # The trusted caller supplies a protected location; no user-supplied paths.
    with sqlite3.connect(database, timeout=5) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS reserved_runs (run_id TEXT PRIMARY KEY NOT NULL)"
        )
        try:
            connection.execute("INSERT INTO reserved_runs(run_id) VALUES (?)", (request.run_id,))
        except sqlite3.IntegrityError:
            return False
    return True
