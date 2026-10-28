# Sonny ONE — Low-Touch Development Protocol
Version: 0.1 | 2026-10-15

## Owner intent
Maximize routine AI-assisted development while minimizing owner interruptions and out-of-pocket spending. This document is a working policy, not evidence of autonomous background execution.

## Allowed without further owner approval
- Develop on feature/sonny-one-foundation or new research feature branches.
- Add code, documentation, deterministic tests, CI checks and prototype UI.
- Inspect failures, fix regressions, and prepare reviewable changes.
- Use existing free tools and services within already granted permissions.
- Keep a change log, test evidence, and next-action queue.

## Require explicit owner approval
- Any paid service, purchase, API charge, or recurring expense.
- Merging into main, production deployment, public launch, or App Store submission.
- Connecting private user accounts, importing personal data, changing sharing permissions.
- Security-sensitive configuration, secret creation or access-policy changes.
- Any external customer-facing communications or irreversible actions.
- Modifying frozen research baselines.

## Development order
1. Verify CI and fix test failures.
2. Build a responsive browser chat UI with a deterministic local demo mode.
3. Add a secure authenticated backend and consent-based persistent memory.
4. Connect a licensed model API under hard spending limits after owner approval.
5. Add PWA installability and iPhone/Windows browser tests.
6. Pilot with test users, monitor quality, cost and privacy; only then consider paid distribution.

## Progress reporting
Every meaningful change should include commit ID, tests run and results, remaining blockers, and whether the owner must act.
Do not report tests as passed until a runner actually reports success.
Never imply continuous autonomous work merely because ChatGPT remains open.

## Research integrity
Frozen SEB-1.0, CSAT-1.3 and RSI v1.3 are read-only.
Keep experimental self-improvement separate from production and require human approval for promotion.


## Low-usage Work/Codex execution policy — 2026-10-24

Applies to all further Sonny ONE research development sessions, especially
`research/apl-001`. This policy controls engineering behavior; it does not
change account tier, model selection, billing settings or product quotas.

1. **Milestone-based work:** Batch closely related code, regression tests and
   documentation into a coherent milestone. Avoid one-commit-per-small-edit
   churn; don't generate status-only commits unless needed to preserve evidence.
2. **Cheap-first tool routing:** Use efficient available models/settings for
   routine inspection, refactoring and test maintenance. Escalate to a stronger
   reasoning configuration for high-risk security reviews, hard debugging and
   architecture changes. Do not assume the assistant can modify host model
   settings or usage allowances.
3. **Minimal tool calls:** Read the current branch HEAD and relevant paths once,
   then reuse observed SHAs and file contents. Do not repeatedly fetch the
   same repository tree. Avoid unnecessary speculative tool calls.
4. **Tests before commit:** Run fast targeted offline/local tests first, then
   the complete local suite when dependencies are available. Fix known failures
   before publishing. Remote GitHub CI is the independent verification gate,
   not a replacement for local testing.
5. **CI economy:** Publish one grouped change after local verification; check
   actual GitHub Actions conclusions once near completion (and as necessary
   for genuine failures). Do not flood CI through trivial documentation commits
   or rapid polling. Never claim a pending workflow passed.
6. **Security first:** Never bypass security tests, provenance checks, review
   boundaries, isolation rules, or evidence requirements to save usage.
   No production promotion, deployment, secret access, paid API/service, or
   frozen-research modification without explicit owner approval.
7. **Stop rules:** Stop at a real infrastructure/permission blocker, an
   exhausted session allowance, a necessary owner approval, or when further
   work would be repetitive with little testable value. Work other independent
   tasks first if productive.
8. **Handoff:** Leave a concise checkpoint with exact branch/commit, tests
   *actually run* and their results, remaining blockers and the next concrete
   task. Keep the standing task queue up to date when priorities materially
   change. Do not repeatedly ask the owner to type "Continue".
9. **Cost discipline:** Use existing free resources and no unapproved
   expenditure. Optimize for verified, security-reviewed improvements per
   execution cycle, not commit count or agent activity.
10. **Truth in status:** Scheduled or persistent background development must
    not be implied without a real operating task/session. Work sessions and
    ordinary ChatGPT conversations are not unlimited autonomous agents.
