# Sonny ONE + Sonny Business — Resume Checkpoint
Date: 2026-10-27

This is a handoff checkpoint, not a claim that unverified tests passed.

## Repositories and branch separation
- Repository: s58hjw2twn-netizen/Sonny2
- Research branch: research/apl-001
- Commercial planning branch: commercial/sonny-business-mvp
- Do not merge or deploy. Keep commercial code separate from experimental APL.
- No paid calls, charges, or production promotion authorized.

## Latest unattended-controller work
- Commit 33e97a96: unattended GitHub coding plan documentation.
- Commit 18b2352a: fail-closed runner preflight regression test.
- Commit d06268e3: updates .github/workflows/sonny-development-controller.yml to run that new regression test.
- At last check, workflow run 40534121179 (APL policy checks for 18b2352a) passed; full suite run 40534121477 was still in progress. The later workflow commit d06268e3 had not yet been checked for CI results.
- Current controller remains read-only: task planning and handoff only. runner_available() returns False; no authenticated coding runner is connected. No unattended patch generation or controller-only commits are enabled.
- Existing live Gemini coding trial workflow is manual/read-only and requires operator-provided GEMINI_API_KEY; no live success should be claimed without checking the latest run and evidence.
- Next steps: verify CI for d06268e3; run offline controller/preflight tests; inspect and run the manual live Gemini/Docker trial only with operator-configured secret; verify real candidate patch and independent tests; keep candidate without credentials and hidden tests; only then consider tightly scoped controller-only research-branch commits. Never enable auto-merge/deploy or alter frozen baselines.

## APL-001 research state
- Candidate archive validation and tests, canonical holdout manifests, request/response binding, review-only evidence intake, unsigned attestation builder, and independent evaluator security contract were added in prior commits.
- Relevant prior commits include 0b352d2d, 23f44b54, 31df2033, 0f4dcffb, 02b171f1, f5e9bdba, b022b0bb, 673b54bb, 78cee13d, e8b5429f, 782e8970.
- Earlier CI passed for prior milestones, including full suite and policy checks at 23f44b54 and policy check for evaluator security contract. Check current run status before asserting latest changes pass.
- Actual independent evaluator, protected external signing-key custody, confidential holdout execution, and a verified end-to-end live coding cycle remain unproven/incomplete.
- No automatic production promotion. Preserve frozen research baselines.

## Sonny Business commercial plan
- Branch: commercial/sonny-business-mvp (created from main; no merge/deployment).
- Target: owner-operated small home-service businesses (cleaning, landscaping, pressure washing, mobile detailing).
- First workflow: manual inquiry intake -> extract details/missing info -> draft response/quote using approved business profile -> owner approval -> follow-up tracking -> basic reporting.
- No autonomous email/SMS sending in v0; no binding quote, booking, payment processing, or production self-modification.
- Pricing hypotheses only: Starter $99/month, Business $199/month, optional onboarding $149-$299; validate costs and willingness to pay before publishing.
- Planning docs: docs/sonny-business-mvp.md (commit 3d1b7881); docs/sonny-business-customer-discovery.md (commit 0c0c628b); docs/sonny-business-build-gate-1.md (commit 7d64ee12); synthetic inquiry fixtures tests/fixtures/sonny_business_synthetic_cases.json (commit 59b1518f).
- These are planning/fixture artifacts, not a functioning commercial application. No live customer data or paid model API used.
- Next: inspect commercial branch tree and existing framework, implement the smallest runnable synthetic-data inquiry-to-draft flow, add mock provider and schema tests, enforce tenant isolation/audit/deletion controls, then test before pilot.

## General constraints
- Free resources first; do not incur charges.
- Do not merge, deploy, enable unattended scheduled coding, or modify production/main.
- Candidate code must never receive repository write tokens, provider credentials, signing keys, or hidden tests.
- Do not claim ongoing autonomous development, real RSI, sentience, deployment, independent evaluation, or tests passing without current evidence.
