# Low-touch development checkpoint — 2026-10-16 UTC

Branch: `feature/sonny-one-foundation`. This continuation starts at `aca1c4c`.

## Completed

- Prior foundation: complete deterministic CI suite and zero-cost local demo.
- Browser checks now run successfully after using a download mirror for the
  optional test-only browser tool (Playwright 1.51.1 / Chromium 134 on Linux).
  The application has no dependency on that testing tool or browser version.
- Fixed edited drafts being discarded when an earlier reply arrives; malformed
  replies do not add partial transcript entries.
- Invalid saved records are rejected visibly. New/erased conversations show a
  usable empty state; replies have accessible busy/status feedback.
- Demo intents match words, avoiding unrelated substring-triggered replies.
- Added PWA manifest/icon and a static offline shell. User/API data is never
  added to the service-worker cache. Offline sends preserve drafts.
- Added automated loopback server lifecycle for browser checks, CI JavaScript
  syntax checks, and the next-action queue.
- Prepared a concrete local authentication and persistent-memory plan; no live
  auth policy, signing secret or private account was created/changed.

## Verified evidence

- `python -m pytest -q`: 48 passed; one third-party Starlette/AnyIO deprecation
  warning. Existing Gate 1 and Sonny ONE research tests remain passing.
- `python scripts/check_sonny_one_browser.py`: 4 viewport suites passed:
  1440×1000, 768×1024, 390×844 and 320×740, using the optional local Playwright
  installation. Covers planning, memory save/forget, persistence opt-in, erasure,
  safe HTML-like text, connection retry, corrupted saved data, in-flight drafts,
  malformed replies, offline reload and API-cache exclusion.
- Inspected rendered desktop and phone screenshots; no horizontal overflow.
- JavaScript syntax checks and `git diff --check`: passed.
- Direct GitHub Actions API confirms prior commit `aca1c4c` completed successfully:
  https://github.com/s58hjw2twn-netizen/Sonny2/actions/runs/38839681730
  (The connector's workflow lookup returned no runs; the direct API supplied
  the verification.) New-commit CI must be checked after its branch update.

## Remaining limits / blockers

- Linux Chromium viewport tests are not physical iPhone, Safari or Windows tests.
- WebKit binary downloaded, but required system libraries are missing. The
  dependency installer failed with container setgroups/seteuid permission errors.
- Home-screen installation on actual iPhone is unverified. Browser shell support
  does not establish App Store readiness or a deployed service.
- No authenticated multi-user backend, server memory persistence or general AI
  replies are enabled in this demo. Legacy X-User-ID routes are not authentication.

## Owner decision

Review AUTHENTICATED_BACKEND_PLAN.md to approve the next local authentication,
access-policy and signing-configuration step under LOW_TOUCH_DEVELOPMENT.md.
No spending, public deployment, main merge or frozen-benchmark change is needed.
See NEXT_ACTIONS.md for dependencies and remaining tasks.
