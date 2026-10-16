# Sonny ONE next-action queue

Updated 2026-10-16 UTC. Branch: `feature/sonny-one-foundation`.
**Pause requested by owner after the current authentication/persistent-memory part.**
Finish commit/CI verification, then stop. Resume only when the owner asks.

## Completed at this pause

- Responsive deterministic demo and static offline/PWA shell.
- Chromium checks at 1440, 768, 390 and 320 pixel widths.
- Separate local authenticated pilot with scrypt passwords, revocable signed
  sessions, Origin/Host/loopback checks and per-account SQLite workspaces.
- Browser UI for login/logout, goals, approved memory, correction, forgetting,
  restart restoration and workspace erasure.
- Duplicate-retry protection, atomic saved turns, bounded history and memory.
- Local launcher creates private signing configuration; Windows entry point added.
- 62 Python tests passed; four demo viewport suites and two authenticated-pilot
  viewport suites passed on Linux Chromium.

## Resume queue

| Priority | Action | Dependency |
| --- | --- | --- |
| 1 | Review saved checkpoint and latest CI result | Owner resumes work |
| 2 | Run Windows launcher and real iPhone/Safari tests | Access to those devices; no public deployment assumed |
| 3 | Select and connect a licensed model runtime | No runtime is installed/connected; paid API use still needs separate approval |
| 4 | Independent security review and private-pilot hardening | Before real personal data or any hosted test |
| 5 | iPhone installation and approved device-access plan | Authenticated pilot deliberately has no private-data offline cache |
| 6 | Private test-user pilot | Owner approves participants/data and any hosting |

The owner approved the local login/access-policy and signing-configuration scope
on 2026-10-15. No paid service, model API charge, public deployment, main merge,
private-account connection or frozen-benchmark change is authorized by that step.

## Remembered hosted demo location

Confirmed read-only on 2026-10-16 UTC: the original Railway webpage is
https://sonny-assistant-0-1-0-production.up.railway.app in project **Sonny Live AI**,
service `sonny-assistant-0-1-0`. The address remains assigned, but the service is
**OFFLINE**, with no active deployment. Its latest deployment is `REMOVED`, last
updated 2026-10-09 at 03:07:08 UTC (October 8 at 11:07 p.m. Eastern). The available
records do not establish why it was removed.

The owner asked to remember this location and status. Do not restart or redeploy
the hosted app without explicit approval: hosting charges may resume. No Railway
settings were changed during the lookup. Development remains paused as above.
