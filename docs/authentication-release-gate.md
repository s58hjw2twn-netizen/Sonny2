# Sonny ONE authentication rollout gate (research only)

Status: NOT APPROVED FOR PRODUCTION. This document is a checklist, not evidence of passing tests.

## Implemented on research/apl-001
- Signed HS256 bearer token required on project/chat/memory/action routes.
- X-User-ID is treated only as an optional consistency check, not authentication.
- Tokens require sub, iat, exp and a matching existing account.
- SONNY_AUTH_SECRET must be at least 32 UTF-8 bytes; absent/short secrets fail closed.
- New /users registrations issue a 24-hour token; the browser persists it in localStorage.
- Isolated GitHub Actions workflow runs auth regression tests on relevant pushes.

## Known blockers
1. No persistent account credential, login, or verified recovery process. Creating a user is not equivalent to proving identity of a prior user.
2. Tokens expire after 24 hours with no renewal or refresh; older Safari workspaces created before this change have no token and cannot resume automatically.
3. Tokens in localStorage are exposed to any same-origin script injection. Prefer an HttpOnly Secure SameSite session cookie and CSRF controls in a future design.
4. No per-account session revocation, signing-key rotation plan, signup rate limiting, or password-reset safeguards.
5. No confirmed successful CI run yet. Do not interpret the absence of a PR-triggered run as push-workflow success.
6. No verified migration plan for existing user/project data; NEVER delete the persistent SQLite volume to solve authentication issues.

## Release gate
- CI and local integration tests pass on the exact release commit.
- Independently review all routes for authorization and project ownership.
- Add account login/recovery and renewal with appropriate abuse controls.
- Test migration with a backed-up copy of existing data, including iPhone Safari refresh and expiry.
- Verify secret provisioned through protected deployment configuration without logging it.
- Review rollback and database compatibility; keep the existing deployment unchanged until explicit production approval.
- Do not merge into main, deploy publicly, incur charges, or modify frozen research without user approval.
