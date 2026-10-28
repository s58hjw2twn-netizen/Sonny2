"""Operator-only test-account provisioning. Never prints passwords or tokens."""
import argparse
import getpass
import sqlite3
from sonny_one.pilot_store import PilotStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='sonny_one_pilot.db')
    parser.add_argument('username')
    args = parser.parse_args()
    password = getpass.getpass('Test-account password (12–128 characters): ')
    if password != getpass.getpass('Confirm password: '):
        parser.error('Passwords did not match')
    try:
        PilotStore(args.db).create_user(args.username, password)
    except (ValueError, sqlite3.IntegrityError):
        parser.error('Account not created: check username, password requirements and whether the account already exists')
    print('Local test account created. No external account was connected.')


if __name__ == '__main__':
    main()
