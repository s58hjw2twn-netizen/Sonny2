# AUTH-001 — Unified Sonny ONE account architecture

Status: IMPLEMENTATION IN PROGRESS — not tested, deployed, or security-audited.
Branch: `security/auth-001`

## Product decision
Build one commercial-ready multi-account system. Initially allow only the founder's account; later invite beta users and eventually enable verified public registration. Do not fork a personal edition.

## Identity and authorization
- Preserve existing `users.id` values as immutable principals; all projects, memories, messages, actions and traces remain scoped to the authenticated user.
- Store independently salted password verifiers in an additive `auth_credentials` table keyed by `user_id`.
- Multiple users may have credentials. Re-enrollment of an existing user must fail; password changes require a separate authenticated recovery flow.
- Authentication must derive identity from a verified server-side session. Never trust `X-User-ID`, localStorage IDs, or client-submitted owner IDs as authority.
- Require project ownership checks on every nested resource. Default-deny all protected routes.
- Prefer secure HttpOnly SameSite cookies, server-side session revocation and CSRF protection; require HTTPS outside local development.
- Rate-limit login, enrollment and recovery; avoid account enumeration and secret-bearing logs.

## Enrollment modes
1. **Private founder enrollment:** local administrative bootstrap only, with explicit proof of control and backup of existing SQLite data. Bind to the correct existing user ID; never infer ownership from a display name.
2. **Invite-only beta:** verified invitation and email ownership, unique account identity, no cross-account access.
3. **Commercial registration:** verified email, recovery, optional MFA/passkeys, abuse controls, privacy policy and operational readiness.

Public `POST /users` name-only enrollment must be disabled as part of API migration. No self-service account creation until verified registration is implemented.

## Migration and release gates
- Inventory and back up the database; implement versioned, additive schema migration.
- Introduce credential persistence and authentication dependencies.
- Add login/logout, secure sessions, expiry and revocation.
- Migrate all FastAPI routes and iPhone web UI; remove client-supplied identity authority.
- Test anonymous denial, token/session forgery, expiry, CSRF, brute-force protection, cross-user resource isolation, duplicate enrollment, and data preservation.
- Run CI and a separate security review before deployment or merge. No security claims from unexecuted tests.
- Do not use quarantined SONNY ONE EVAL 001 as a development test or benchmark.

## Commercial capabilities deferred until needed
Email verification, invitations, recovery, billing/subscription entitlements, quotas, tenant administration, production database operations, observability and incident response.

## Current code status
`sonny/credentials.py` and `sonny/identity_store.py` are isolated foundations only. They are not wired to the API; current `X-User-ID` endpoints remain insecure. Keep this branch out of production until the release gates are met.
