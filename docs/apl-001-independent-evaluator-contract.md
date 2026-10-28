# APL-001 Independent Holdout Evaluator — Deployment Contract

Status: design specification only. This document does not claim that an independent
service is deployed, that private tests are confidential, or that any result is trusted.

## Trust boundary
- Candidate generation and candidate execution are untrusted.
- The holdout evaluator must run in a separately provisioned account/project or
  isolated runner controlled independently from candidate code.
- Do not mount the evaluator's private fixtures, signing key, credentials, home
  directory, container socket, or repository write token into candidate execution.
- Candidate input is an immutable archive addressed by SHA-256 plus a pinned base
  revision and suite digest. Reject archives exceeding configured size/file-count
  limits, path traversal, symlinks, special files, and unexpected file types.
- The evaluator fetches or receives only the candidate artifact; it never accepts
  executable test commands or test definitions from the candidate.
- Candidate execution has no network, non-root identity, dropped capabilities,
  read-only root filesystem, bounded CPU/memory/PIDs, strict timeout, and disposable
  workspace. Do not treat these flags alone as a complete sandbox boundary.
- Holdout fixtures remain outside the candidate container. A trusted evaluator
  harness invokes tests and returns only bounded pass/fail/error summaries.
- The signing private key is provisioned and held by the evaluator operator, never
  supplied by candidate code, model prompts, GitHub Actions candidate jobs, or a
  response payload. Prefer an OS/KMS-backed signing operation when available.
- Sign a canonical, versioned payload binding candidate SHA-256, base revision,
  suite SHA-256, evaluator identity, result, timestamp, and run nonce.
- The controller pins evaluator identity and public-key fingerprint out of band,
  verifies the signature and request binding, and rejects replayed nonces.
- Evaluation results are evidence for human review only. No merge, deployment, or
  production promotion is triggered by a PASS.

## Required acceptance tests
1. A candidate attempting to read known fixture paths cannot access holdout bytes.
2. Candidate has no provider credentials, GitHub token, network access, or signing key.
3. Altered candidate digest, suite digest, revision, evaluator identity, result, or
   nonce causes signature/request verification failure.
4. Replayed signed attestations are rejected.
5. Timeout, crash, resource exhaustion, malformed archive, and evaluator error
   return ERROR and never PASS.
6. Two independent reviewers can reproduce the attestation verification from
   captured artifact, canonical payload, pinned public key, and logs.
7. The evaluator emits no raw hidden-test contents in logs or response bodies.

## Promotion gate
Promotion remains disabled until the acceptance tests pass on a genuinely separate
evaluator and a human explicitly authorizes a specific reviewed commit. This file is
a checklist, not proof that any acceptance test has run.
