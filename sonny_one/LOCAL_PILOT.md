# Sonny ONE authenticated local pilot

This is a local test-account prototype with deterministic demo replies. It does
not call a model API, use a paid service, connect private accounts or run research.
Owner approved the local authentication and signing-configuration step on
2026-10-15, New York time. Production and public deployment remain unapproved.

## Start on Windows 11

1. Check out `feature/sonny-one-foundation` with Python 3.12 installed (the tested runtime).
2. Open `Start-Sonny-ONE.cmd` from the repository folder. It creates a local Python
   virtual environment and installs the pinned free Python dependencies.
3. On first run, choose an invented test username and password (12–128 characters).
   Password entry is hidden. The launcher creates and retains a private random
   signing key without printing it.
4. The launcher opens http://127.0.0.1:8766. Sign in using that test account.
   Keep the terminal window open; Ctrl+C stops the server.

The Windows launcher source has been reviewed, but it has not been executed on a
real Windows computer in this environment. The Python backend, local launcher
configuration, and browser flows were exercised on Linux.

## Start from a Python environment

```sh
python -m pip install -r requirements.txt
python scripts/start_sonny_one_pilot.py
```

Use `--no-browser` to open the URL yourself, or `--port 8767` to choose a different
unprivileged loopback port. Local configuration and SQLite data live in the
ignored `local_state/` folder. Do not commit/share that folder. Files get private
POSIX permissions on creation; Windows privacy depends on the user's filesystem
ACLs. Storage is unencrypted; use sample data only.

To add another invented test account:

```sh
python -m sonny_one.pilot_admin --db local_state/pilot.db bob-demo
```

For direct Uvicorn configuration, set `SONNY_ONE_AUTH_SECRET` (private random
value, at least 32 characters), `SONNY_ONE_DB`, and exact `SONNY_ONE_ORIGIN`, then:

```sh
python -m uvicorn sonny_one.pilot_app:create_app --factory --host 127.0.0.1 --port 8766 --no-proxy-headers
```

The app rejects non-loopback clients, unexpected hosts and cross-origin writes.
Do not change the bind address or configure a public reverse proxy.

## Supported behavior

- Test-account passwords use unique salts and scrypt hashes. No open signup.
- Signed, HttpOnly, SameSite=Strict, host-only cookies expire after one hour.
  Sessions can be revoked and logout invalidates the server record. HTTP cookies
  are permitted only on loopback; configured HTTPS origins use Secure cookies.
- Goal, last 100 conversation messages and up to 50 explicitly approved facts
  persist per account. Browser localStorage is not used by this signed-in UI.
- Save goal explicitly. Save approved fact is the memory-consent action. Correct
  requires approving a new value; stale revisions are rejected. Provenance and
  approval time are stored; a correction event records that it happened, without
  keeping the replaced statement in the memory event table.
- Forget removes a fact and future recall. Existing chat quotations remain until
  New conversation or Erase workspace. Chat history is not used as approved memory.
- Erase workspace clears that account's goal, conversation, facts, fact events
  and retry records. It retains the login account and session. This is application
  deletion; filesystem backups and forensic erasure are not managed by the app.
- Chat retries reuse a request ID to avoid duplicate saved turns. Failed database
  transactions leave no partial turn. No general AI response is available yet.

## Validation

```sh
python -m pytest -q
# Optional: Playwright + Chromium must already be installed
python scripts/check_sonny_one_browser.py --pilot
```

The browser runner creates two disposable invented accounts in a temporary DB,
starts a loopback server with a public test-only signing key, runs checks, and
removes the temporary state. It never uses operator configuration or real data.

The stateless demo at `sonny_one.web_app:app` remains separate. Its offline/PWA
shell is not activated by the authenticated pilot; private workspace responses
are marked no-store and are not cached in a service worker. Safari, Windows and
actual iPhone installation remain unverified.

## Remaining release gates

Independent security review, broader browser/device testing, credential recovery,
encrypted backups/retention policy, and production hosting controls are not
complete. Never expose this prototype publicly based only on its local tests.
A licensed model runtime/provider is still needed for useful general chat. Any
paid API use needs separate owner approval and cost enforcement first.
