# AUTH-002 implementation review — outstanding release blockers

Status: INCOMPLETE / UNTESTED. Branch only; do not merge or deploy.

## Implemented
- Database-backed opaque sessions with hashed tokens, expiry and revocation.
- Cookie login/logout and CSRF header checks on authenticated unsafe routes.
- Project, memory, chat and action APIs now derive identity from the session.
- Name-only public account creation is disabled.
- Browser uses password login; no session token in localStorage.
- New isolated authentication tests are committed but not executed.

## Blockers before merge or deployment
1. Existing `tests/test_gate1.py` expects `POST /users` and `X-User-ID`; update these functional tests to authenticate without using quarantined scientific benchmark material. Existing suite will not pass unchanged.
2. Implement rate limiting/lockout on failed login attempts and generic error behavior.
3. Add explicit secure administrative owner-enrollment command and documented database backup/restore process. There is no public registration and no account can log in until a credential is enrolled through trusted administration.
4. Implement safe session restoration after page reload. Current browser intentionally requires re-login and creates a new project at each sign-in; replace with authenticated project selection and reuse.
5. Test login CSRF, hostile Origin/Host and reverse-proxy HTTPS configuration; do not use `SONNY_ALLOW_HTTP_LOCAL=1` outside localhost development.
6. Add tests for session expiry, revocation, multiple sessions, cross-account object IDs, cookie attributes and all API endpoints.
7. Run test suite in CI and obtain a security review. Tests in this branch have not been executed.

## Deployment constraint
The `main` branch is unchanged. The development branch must not be exposed publicly until the blockers above are resolved.
