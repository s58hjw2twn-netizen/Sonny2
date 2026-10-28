# Sonny ONE Chat Bridge — Phase 1 security and integration contract

Status: **local prototype, not deployed, not connected to ChatGPT**.

## Verified scope
- `sonny_one/chat_bridge.py` exposes GET `/v1/status` and GET `/v1/capabilities`.
- Both endpoints require `Authorization: Bearer <token>`.
- A secret of at least 32 characters is required at startup. Never commit or print it.
- No user memories, personal records, GitHub write operations, model calls, or autonomous commits are exposed.
- `/v1/capabilities` is a **static inventory**, not live capability attestation.
- An operator-supplied revision is labeled **not independently checked**.
- There is no external-facing deployment or authenticated ChatGPT tool registration.

## Threat model and deployment blockers
1. **Transport security:** Bearer tokens are replayable. Never expose this API over plain public HTTP. A secure HTTPS termination and credential-rotation mechanism must be designed and tested before remote use.
2. **Network isolation:** Phase 1 does not enforce loopback-only access. Run only on a trusted, non-public development interface. No internet-facing deployment is authorized.
3. **Authorization:** One static token is not per-user identity. Do not expose private memory or multi-user state until per-user authorization, consent, revocation, and cross-account isolation are verified.
4. **Evidence integrity:** Do not equate static capability declarations or operator-supplied commit SHAs with independently verified runtime evidence.
5. **Rate limits and audit:** No per-client rate limits, durable security event log, or credential rotation is implemented. Do not treat the prototype as production hardened.
6. **Actions:** All external actions, code commits, merges, and deployments remain out of scope. Never grant the bridge GitHub write credentials.
7. **Tests:** CI passing verifies the implemented tests, not security against all attacks. The 22 skipped full-suite tests require review.

## Local-only verification
With a disposable test secret, run:

```bash
python -m pytest -q tests/test_sonny_one_chat_bridge.py
python -m pytest -q
```

Do not run an externally reachable service until a separate security review and explicit owner approval.

## Phase 2 acceptance gates
- TLS-only remote transport, revocable credentials, explicit identity and authorization design.
- Origin/proxy/host boundary and abuse controls tested.
- Security tests for missing, invalid, revoked, and leaked credentials.
- A trusted source of live commit/CI evidence, not caller-provided attestations.
- Documented ChatGPT plugin tool contract and user-mediated connection.
- No write or memory capability without separately approved scope and independent verification.

The Chat Bridge is **not** an installation of Sonny ONE inside GPT-6; it is a future tool boundary for selected, auditable functionality.
