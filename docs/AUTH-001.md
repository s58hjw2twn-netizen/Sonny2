# AUTH-001 — Personal-first authentication architecture

Status: PROPOSED — design only; not implemented or security-validated.
Target branch: `security/auth-001`
Scope: Personal owner access now, multi-user commercial accounts later.

## Current findings
- `sonny/app.py` trusts a client-provided `X-User-ID` for protected project, chat, memory and action routes.
- `sonny/auth.py` contains JWT issuance and verification helpers, but protected routes do not use them.
- The web UI creates an unauthenticated user through `POST /users` and stores a user ID in localStorage.
- Existing database records are keyed by user IDs and project ownership; preserve these identifiers during migration.

## Security goals
1. Reject unauthenticated requests to protected endpoints.
2. Resolve the acting user only from a verified session or signed token, never a client-selected user ID.
3. Preserve existing project, memory, message and action ownership.
4. Support one owner initially without baking a single-user assumption into storage or authorization.
5. Support commercial multi-user enrollment and recovery later without replacing ownership IDs.
6. Never commit credentials, API keys, signing secrets or password hashes derived from real credentials.

## Proposed personal-release design
- Introduce an explicit owner-enrollment procedure, disabled after successful enrollment. Enrollment must require an out-of-band, server-side bootstrap secret or local administrative action; public name-only signup cannot create a privileged owner.
- Store a password hash using a modern, salted password KDF (prefer Argon2id), never plaintext. Add a credentials table linked to existing `users.id`.
- Provide login and logout flows. Prefer an HttpOnly, Secure, SameSite cookie with server-side revocation/rotation, plus CSRF defenses for state-changing requests. If bearer JWTs are retained, add revocation/rotation strategy and avoid localStorage token persistence.
- Use FastAPI dependency injection for authenticated identity on every protected route. Retire `X-User-ID` as an authority; ignore or reject it.
- Preserve `require_project(authenticated_user_id, project_id)` authorization checks on all nested resources.
- Add rate limiting and generic login errors. Require HTTPS outside localhost.
- Keep `OPENAI_API_KEY`, signing secrets and bootstrap secrets server-side.

## Migration and compatibility
1. Inventory the existing users/projects and back up the SQLite database before schema changes.
2. Provide an explicit, audited mechanism to bind the current owner's existing `users.id` to the new credential; do not silently claim or merge records by display name.
3. Create additive, versioned schema migrations with rollback/backup instructions.
4. Update browser onboarding, login, session restore and logout; never rely on a stored user ID for authentication.
5. Keep personal owner registration closed after enrollment; commercial self-registration is a separate future feature.
6. Ensure old clients cannot bypass the new authentication checks.

## Acceptance tests
- Anonymous requests to all protected endpoints return 401.
- Invalid, expired and revoked sessions are rejected.
- A valid owner cannot switch identity by supplying another `X-User-ID`.
- Direct object identifiers for another user/project are denied.
- Owner's existing project and memory remain accessible after explicit migration.
- Passwords, cookies, credentials and secrets do not appear in traces or logs.
- Session expiration, logout, login throttling and CSRF controls are exercised.
- Browser sign-in and chat flows work on a mobile viewport.
- Tests are run in CI and results are recorded; passing tests are not equivalent to a security audit.

## Commercial extension (later)
- Controlled registration and verified email ownership.
- Account recovery and optional MFA/passkeys.
- Tenant-aware authorization, abuse prevention and privacy controls.
- Production-grade database migration, backups and operational monitoring.

## Non-goals for this design commit
- No route, database, or UI behavior changes.
- No deployment, test execution, or security certification.
- No changes to SONNY ONE EVAL 001 benchmark materials or blind-evaluation protocol.

## Next implementation slice
Implement the authenticated-user dependency and credential/session storage on this branch, with focused tests, then migrate the browser UI and verify existing data preservation before considering merge.
