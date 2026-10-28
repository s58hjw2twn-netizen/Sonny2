# Sonny ONE — Unattended GitHub Coding Controller Plan

Status: implementation plan; unattended coding is NOT enabled by this document.
Target branch: research/apl-001. Production/main remains out of scope.

## Current verified boundary
- `.github/workflows/sonny-development-controller.yml` currently has `contents: read`; it validates the controller, emits a task plan/handoff, and does not generate, test, or commit model-authored code.
- `.github/workflows/live-gemini-coding-trial.yml` is manual-only, read-only, and expects `GEMINI_API_KEY`; it runs the live coding trial in Docker but does not commit the candidate.
- Therefore, a complete unattended GitHub coding loop is not yet operational.

## Required architecture
1. Trusted scheduler/controller selects one bounded, allowlisted task from a reviewed backlog on `research/apl-001`.
2. Controller sends only the task specification and approved source context to a coding-model adapter. Do not expose GitHub write tokens, CI secrets, hidden tests, or signing keys to the model or candidate process.
3. Candidate output is a patch artifact, not a direct repository write. Reject oversized patches, path traversal, forbidden paths, workflow/permission edits, dependency changes outside allowlist, and modifications to frozen baselines.
4. Apply candidate patch in a disposable workspace with no network, no secrets, no Docker socket, non-root execution, resource limits, and a strict timeout.
5. Run deterministic tests first, then held-out evaluation through a separately trusted evaluator. Candidate process cannot read hidden tests or alter evaluator code.
6. A separate trusted controller verifies test evidence, diff policy, scope, and lineage. It alone may commit to a dedicated research branch. The candidate process never receives write credentials.
7. Every commit includes task ID, parent SHA, patch SHA-256, model/provider/model ID, test report hashes, evaluator attestation, and explicit `promotion=FORBIDDEN` metadata.
8. Failed, ambiguous, untested, or policy-changing patches are rejected and logged; retry budget and spend cap are mandatory.
9. Main, release branches, deployment workflows, secret stores, and commercial product branch are explicitly denied.
10. Production promotion remains a separate human-authorized action; no auto-merge or deploy.

## Staged activation gates
- Gate A: offline deterministic controller tests; no model key, no writes.
- Gate B: live provider trial with a bounded request budget and a manually configured provider secret; candidate has no secret access.
- Gate C: demonstrate repeated patch -> isolated tests -> independent verification cycles with audit artifacts; still no repository write permission for candidate code.
- Gate D: controller-only, branch-scoped commit permission after independent review of the threat model and successful negative tests. Limit to one commit per run and a fixed daily budget.
- Gate E: scheduled unattended runs only after Gates A-D pass; stop automatically on repeated failure, unexpected diff, missing evaluator evidence, provider errors, or budget cap.

## Acceptance tests before unattended operation
- Candidate cannot read environment secrets, repository tokens, hidden fixtures, or host filesystem.
- Candidate cannot alter tests, workflows, evaluator code, frozen baseline, or protected paths.
- Malicious patch and prompt injection are rejected.
- Missing/failed evaluator result never passes.
- Replayed or mismatched attestations are rejected.
- Controller commits only a tested exact patch digest to the research branch.
- No path from this workflow can merge, deploy, or modify commercial/main branches.
- End-to-end trial is independently repeated and produces reproducible artifacts.

## Immediate next task
Complete the offline controller test suite and inspect the existing development-controller modules before adding any write permission. Then run the existing live Gemini Docker trial manually with an operator-configured secret and confirm its actual CI evidence. Do not add scheduled model calls or branch-write permission until those gates are verified.
