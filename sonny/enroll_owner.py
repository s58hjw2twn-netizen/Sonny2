"""Offline administrative enrollment for an existing Sonny account.

Usage:
    python -m sonny.enroll_owner --db /private/path/sonny.db --user-id UUID

Run only on a trusted machine with the application stopped. Back up the
database before using this command. Never put a password in CLI arguments.
"""
import argparse
import getpass
import os
import sqlite3
import sys

from .identity_store import IdentityStore


def main(argv=None):
    parser = argparse.ArgumentParser(description="Enroll an existing Sonny account offline")
    parser.add_argument("--db", required=True, help="Existing SQLite database path")
    parser.add_argument("--user-id", required=True, help="Verified existing users.id")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.db):
        parser.error("Database file does not exist; refusing to create a new one")

    print("STOP the Sonny server and back up the SQLite database first.")
    print("This operation binds credentials to an EXISTING user ID.")
    confirm = input("Type ENROLL to confirm offline ownership verification and backup: ")
    if confirm != "ENROLL":
        print("Cancelled")
        return 1

    password = getpass.getpass("New account password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords did not match", file=sys.stderr)
        return 1
    if len(password.encode("utf-8")) < 12:
        print("Use a password of at least 12 UTF-8 bytes", file=sys.stderr)
        return 1

    connection = sqlite3.connect(args.db)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        identity = IdentityStore(connection)
        identity.initialize()
        identity.enroll_existing_user(args.user_id, password)
    except (ValueError, sqlite3.Error) as exc:
        print(f"Enrollment failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    finally:
        connection.close()
    print("Credential enrolled for the verified existing account.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
