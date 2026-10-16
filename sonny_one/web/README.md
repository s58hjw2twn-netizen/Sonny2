# Sonny ONE local browser prototype

From the repository root:

```sh
python -m pip install -r requirements.txt
python -m uvicorn sonny_one.web_app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765 on the same computer. This is a separate app from
`sonny.app`; it never loads the legacy model integration or research controller.
No API key, account, paid service, build step or external asset is needed.
Keep it bound to loopback; this prototype has no authentication and is not a
hosted multi-user product.

## What works

- Phone and desktop layouts, keyboard submission, accessible labels and status.
- Deterministic planning, greetings, approved-memory recall and honest fallback.
- Explicitly save and forget sample facts; nothing is learned automatically.
- Optional browser-local workspace persistence, off by default. Enabling it saves
  the goal, approved facts and latest 100 chat messages on this browser profile.
- New conversation clears chat but retains the goal and approved memory.
- Erase workspace clears chat, memory, goal and the stored workspace.
- Retryable connection errors; no transcript entry is added for a failed request.

The server does not persist conversation or memory. Requests contain the current
message, goal and approved facts. Forgetting a fact stops future recall but does
not remove earlier chat quotations; use New conversation or Erase workspace.
Browser local storage is unencrypted; use invented sample data only. Reloading
without opting into browser storage starts fresh.

## Validation

```sh
python -m pytest -q
node --check sonny_one/web/app.js
# Optional, with Playwright and its Chromium browser installed:
node tests/browser_sonny_one.cjs
```

The browser script expects the local server above to be running. It uses desktop
and iPhone-sized Chromium viewports; it does not claim Safari or physical-device
certification. It blocks external web requests and tests persistence, consent,
forgetting, erasure, HTML injection rendering, and network-failure recovery.

## Next queue / approval boundaries

1. Validate on real iPhone Safari and Windows browsers.
2. Design authentication, consent and durable storage for a private pilot.
   Security configuration, secret creation and access policy changes need owner
   approval before implementation under LOW_TOUCH_DEVELOPMENT.md.
3. Add licensed model routing only after approved provider choice and spending
   limits. This demo deliberately has no provider path.
4. Evaluate PWA installability after the persistence and account design is agreed.

No production release or research promotion is implied by passing these checks.
