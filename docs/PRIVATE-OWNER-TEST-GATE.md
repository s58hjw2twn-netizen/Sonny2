# Sonny ONE — private owner test gate

**Target:** One owner can use Sonny in mobile Safari without losing their
account, projects, conversation, or confirmed memories. This is a private
test build, not a public beta or commercial release.

## Automated checks (must pass)

Run each test file in a separate Python process because current tests create
module-level app instances and databases:

```bash
python -m pip install -r requirements.txt
python -m compileall -q sonny tests
python -m pytest -q tests/test_credentials.py tests/test_identity_store.py
python -m pytest -q tests/test_auth002.py
python -m pytest -q tests/test_auth003.py
python -m pytest -q tests/test_gate1.py
```

Do not claim a green build until the actual test output or GitHub Actions job
logs have been inspected. A missing workflow result is not a passing result.

## Manual owner acceptance test

1. Use a backed-up, private SQLite database. Stop the app and enroll the
   **verified** existing owner account offline (see OWNER-ENROLLMENT.md).
2. Set the actual OpenAI API credentials securely in the deployment environment
   (never commit credentials). Verify a live chat reply; mocked unit tests do
   not prove that the model integration works.
3. Host the app behind verified HTTPS and trusted proxy settings. Check that
   browser cookies are Secure, HttpOnly and SameSite=Strict.
4. On iPhone Safari, open the private URL and sign in using the existing user
   ID and password.
5. Create a project and send a real chat message. Verify both messages appear.
6. Propose and confirm a memory. Close Safari, reopen the URL, and verify the
   authenticated session, project, messages and memory are restored.
7. Sign out. Verify that project and chat APIs reject unauthenticated requests.
8. Sign in as a second independently enrolled test user; verify that the
   owner's projects and messages are inaccessible.
9. Restart the application and verify the owner can sign in and recover the
   same data from persistent storage.

## Stop-ship issues

- Any failing automated test, traceback, or unverified test run.
- Any user isolation or CSRF failure.
- Session recovery, project restoration, or persistent storage failure.
- Missing or invalid TLS, incorrect trusted-proxy configuration, or
  inappropriate local-HTTP bypass.
- Missing model API credentials or failing real chat integration.
- Exposing the private owner instance publicly before authorization,
  backup/recovery, and operational review.

## Scope discipline

Until this gate passes, prioritize test failures, runtime crashes, account
enrollment, mobile sign-in, project recovery, real chat, and persistence.
Do not run quarantined EVAL-001 benchmarks. Do not merge to main or deploy
without explicit approval.
