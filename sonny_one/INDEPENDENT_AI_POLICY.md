# Sonny ONE — Independent AI and Proprietary Model Policy
Version: 1.0 | 2026-10-24
Status: Owner-approved strategic direction; implementation milestones remain subject to verification.

## Mission
Build Sonny ONE as an independently operable AI companion, with a long-term objective of a proprietary language model. Do not conflate ownership of the application with ownership of foundation-model weights.

## Engineering requirements
1. Maintain a provider-neutral inference interface. Application, memory, identity, and authorization logic must not depend on a single model vendor.
2. First target a licensed open-weight model, locally or independently hosted, with a deterministic offline fallback for development and tests.
3. No paid inference, hosting, downloads with material cost, deployment, or secret/configuration access-policy changes without explicit owner approval.
4. Document model provenance, weights licenses, redistribution and commercial-use permissions, training-data rights, version hashes, and dependency obligations before integration.
5. Isolate user memory and personal data from model-training datasets by default. Training requires explicit informed consent, a deletion/retention policy, and provenance tracking.
6. Evaluate accuracy, calibration, robustness, privacy, security, latency, and inference cost against fixed baselines. Keep held-out tests separate from training and optimization.
7. Treat fine-tuning, distillation, and training from scratch as separate research milestones. Do not claim an original foundation model when using or adapting third-party weights.
8. Keep recursive software-improvement proposals sandboxed, reproducible, and subject to human approval before promotion. No autonomous production modification or model-weight changes.
9. Preserve frozen SEB-1.0, CSAT-1.3, RSI v1.3, and other preregistered baselines as read-only.
10. Describe self-models, emotional expressions, and companion behaviors as simulated; do not claim consciousness or sentience.

## Milestones and acceptance gates
M1: Inventory inference call sites and add a provider-neutral interface with offline deterministic tests. Acceptance: existing tests pass and adapter contract tests cover failure, timeout, malformed output, and authorization boundaries.
M2: Evaluate a commercially permissible open-weight model under explicit cost and hardware constraints. Acceptance: license review, repeatable setup, benchmark report, and documented fallback.
M3: Investigate licensed-data fine-tuning. Acceptance: consent/data audit, baseline comparison, reproducible training and rollback.
M4: Research proprietary architectures and original model training only when independent evidence supports feasibility and budget is approved.

## Current next action
Inspect research/apl-001 code and CI, identify existing inference entrypoints and test gaps, then implement M1 as a single locally tested milestone. Do not merge to main, deploy publicly, or incur charges. Report exact tests and commit SHA; do not imply implementation is complete merely because this policy is committed.
