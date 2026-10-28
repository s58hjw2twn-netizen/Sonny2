# Sonny ONE checkpoint — 2026-10-23

## Objective
Private, iPhone Safari-accessible Sonny ONE with authenticated conversations, explicit-consent persistent memory, and eventually a real language-model provider. Keep development inexpensive and obtain owner approval before deployment, spending, connecting private accounts, or changing production security configuration.

## Verified
- Branch: feature/sonny-one-foundation (do not merge into main without approval).
- Latest engineering commit at checkpoint: 172a43942c24b8fe66969cf86b993cbf183cdb97.
- Prior commit 2f1f47bdf80204ca19fa97650f6a8dddbffeaad4 passed GitHub Actions complete deterministic suite: 119 passed, 1 deprecation warning; JavaScript syntax checks passed. Foundation workflow also succeeded.
- Local pilot has login, session revocation, consent-based memories, corrections/deletion, conversation persistence, and deterministic demo responses. Its network boundary is loopback-only.
- Hosted config, HTTPS/Origin request boundary, and fail-closed hosted candidate exist. Hosted candidate still returns HTTP 503.
- Draft PostgreSQL schema sonny_one/sql/hosted_schema_v1.sql added at 172a439 with account-isolated workspace/memory/message/turn tables and row-level-security policies. Not migrated, exercised, or independently security reviewed.

## Not yet delivered
- Hosted PostgreSQL repository/data-access integration and migration tests.
- Hosted authentication/session implementation and secure production secret handling.
- Actual hosted chat app connected to the responsive UI.
- Real model provider (requires separate provider/cost authorization).
- Live private Safari URL, iPhone cellular acceptance test, and production security review.
- Backups, encrypted-at-rest verification, retention/deletion operations, deployment rollback.

## Next engineering steps
1. Review schema privileges/RLS assumptions and write PostgreSQL migration and isolation tests against disposable synthetic data.
2. Build hosted database repository and session adapter without changing the local pilot boundary.
3. Wire hosted routes to existing UI and verify end-to-end with synthetic accounts.
4. Validate security, hosting costs, backups, HTTPS proxy trust and iPhone Safari behavior.
5. Seek explicit owner approval before any Railway deployment, secret changes, charges, or real provider integration.

## Operating constraints
No spending, public deployment, main merge, modification of frozen research baselines, or use of real user data without approval. Do not claim the new hosted schema passed CI or database tests until independently verified.
