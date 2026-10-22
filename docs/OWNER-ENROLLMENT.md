# AUTH-003: Safe initial account enrollment

**Development branch only. Do not deploy until CI and security review pass.**

The new sign-in system intentionally does not expose self-service registration. Existing Sonny accounts must be bound to a password offline by a trusted operator who has independently verified the correct `users.id`.

1. Stop the Sonny server and all processes writing to the database.
2. Locate the existing database (usually `sonny.db`, or `SONNY_DB`). Confirm the exact existing user ID from `SELECT id,name FROM users` in a trusted local SQLite session. A display name alone is not sufficient to establish ownership.
3. Back up the SQLite database using SQLite's online backup API or the `sqlite3` CLI `.backup` command. Verify the backup exists and can be opened. Protect the backup as sensitive user data.
4. On the trusted host, with the application still stopped, run:

   ```bash
   python -m sonny.enroll_owner --db /private/path/sonny.db --user-id EXISTING_VERIFIED_USER_ID
   ```

5. Confirm that ownership verification and backup have been completed, then enter and confirm a unique password using hidden prompts. The password is not passed on the command line or written to GitHub.
6. Start Sonny only after the new API and security tests pass. HTTPS is required unless `SONNY_ALLOW_HTTP_LOCAL=1` is explicitly enabled for isolated local development.

The command does not create users, does not select accounts automatically, and rejects a second enrollment for the same user. Existing projects and memories are preserved by the additive credentials table.

## Remaining blockers

- The command does not independently verify identity or create the backup: those are operator responsibilities.
- Rate limiting is account-scoped only, not IP-scoped.
- Existing Gate 1 functional tests still use deprecated unauthenticated account creation.
- Confirm GitHub Actions results and test all sessions, CSRF, and multi-account isolation.
- Reverse proxy configuration, secure cookies and recovery procedures require security review.
