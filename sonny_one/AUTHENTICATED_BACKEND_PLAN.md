# Local authenticated backend — reviewable next implementation

Status: owner approved this local implementation on 2026-10-15 (New York time).
Implemented as a separate local pilot; see LOCAL_PILOT.md. No production policy changed.
Scope: separate Sonny ONE local pilot; invented test data only; no public hosting,
paid providers, private-account connections, email delivery or research execution.

## Current boundary

`sonny_one.web_app` is a stateless demo, with no accounts or trusted user identity.
Browser-approved facts are supplied in each request. They are demonstration
context, not authenticated server memory. The older `sonny.app` uses caller-supplied
`X-User-ID` for its project routes. That header is not authentication, and those
routes must not be reused as the security boundary for a multi-user pilot.
`sonny.auth` exists as a JWT helper but is not wired into those legacy routes.
Passing legacy Gate 1 tests does not establish authenticated isolation.

## Proposed local pilot policy

- Keep the demo and legacy application separate and unchanged in availability.
- New authenticated app must refuse startup when its signing secret is absent.
  No default secret, fallback to caller-supplied identity, or automatic secret
  generation. Owner configures the signing secret only after approving this plan.
- Test-only accounts, created through a local operator command. No open signup.
  Passwords hashed with salted scrypt using Python's standard library.
- Browser login returns an HttpOnly, SameSite=Strict, host-only session cookie.
  Secure cookie enabled for any future HTTPS environment; local HTTP use must
  remain on loopback. Origin checks protect browser writes. No JWTs in localStorage.
- Server sessions have expiration and revocation. Logout revokes the session.
- All object queries include authenticated owner identity. Client-supplied user
  IDs never establish identity. Unowned objects return 404.
- SQLite server memory persists only after explicit fact approval. Track source,
  approval time and ownership. Support correction, forgetting and workspace
  erasure; never automatically promote conversation into memory.
- Do not insert research runtime, simulated emotions or strategy promotion into
  the product request path. Deterministic demo provider remains the only provider.

## Proposed contract

| Route | Purpose | Identity / consent rule |
| --- | --- | --- |
| POST /auth/login | Start session | Operator-created test account; bounded failures |
| POST /auth/logout | Revoke session | Current cookie, browser origin checked |
| GET /api/workspace | Restore owned goal and conversation | Authenticated owner only |
| PATCH /api/workspace | Edit goal | Authenticated owner only |
| POST /api/chat | Store and answer one turn | Only this owner's approved facts |
| POST /api/memories | Save explicit approved fact | Explicit consent plus provenance required |
| PATCH /api/memories/{id} | Correct fact | Owner only; correction trail |
| DELETE /api/memories/{id} | Forget fact | Owner only; excluded from future retrieval |
| DELETE /api/workspace | Erase saved workspace | Owner only; clear data and related memory |

## Acceptance before connecting the UI

1. Missing, expired, forged and revoked sessions rejected; X-User-ID spoofing fails.
2. Two accounts cannot read, edit, correct, delete or chat using each other's state.
3. Persistence survives app restart, with consent and provenance intact.
4. Forgetting removes future influence; erasure removes workspace data.
5. Cross-origin write attempts rejected; cookies and logs do not disclose tokens
   or passwords. Invalid login failures do not disclose whether an account exists.
6. No external network/API calls; complete test suite and browser checks pass.

## Approval boundary

LOW_TOUCH_DEVELOPMENT.md explicitly requires owner approval for
“Security-sensitive configuration, secret creation or access-policy changes.”
The owner granted this local login/session and signing-configuration approval.
The launcher creates private local signing configuration only when run. Tests use
disposable invented accounts and test-only keys. No private accounts are connected. No payment or public deployment is needed for this local step.

Remaining product choices can use the defaults above. No provider or subscription
purchase is needed until a separate model-integration approval.
