# Sonny ONE inference security gate

Status: **local research prototype only**. No external model transport, API key,
paid provider, or production inference endpoint is configured.

## Verified design boundaries

- The public Safari Pages application is static and scripted; it does not use this Python API.
- `/api/inference/demo` is deliberately unauthenticated but offline-only.
- `/api/inference/private` reuses the repository's JWT authentication dependency.
- Authenticated requests are subject to an in-process per-user sliding-window limit.
- Provider exceptions and timeouts map to sanitized HTTP 503/504 responses.
- A caller-side deadline is not a hard cancellation of a blocking provider operation.
- External inference remains fail-closed in `inference_config.py`.
- No secrets may be placed in client JavaScript, Pages assets, or Git history.

## Required before exposing a real model

1. Require authentication and authorization on every real-model route; disable or isolate unauthenticated model access.
2. Implement provider-native connect/read timeouts, bounded concurrency and hard resource quotas. A timed-out worker thread can continue running.
3. Replace the in-memory limiter with a shared limiter, and add IP/account/device abuse controls without trusting spoofable forwarded headers.
4. Enforce per-user usage and spending caps on the server; keep external inference disabled until explicitly approved.
5. Validate deployment secrets at startup, enforce TLS and a restrictive host/CORS policy, and prevent debug tracebacks.
6. Add privacy review, retention limits, audit trails, and prompt-injection containment before tool use or persistent memory.
7. Perform independent adversarial review and verify all CI gates before any deployment decision.

## Local verification

Run `python -m pytest -q` from the repository root. The `sonny_one/test_inference_route.py`
suite covers valid/invalid JWTs, missing-secret behavior, provider errors,
rate limiting, and provider non-invocation on unauthorized or throttled requests.

This document is a gate checklist, **not** a security certification.
