# Sonny ONE — Independent AI Track (90-day target)

Status: development plan; not evidence of a trained or deployed model.

## Goal
Ship a private, working Sonny ONE with an independently runnable, open-weight
language model. Preserve the existing animated iPhone prototype and frozen
research baselines. Do not imply that adaptation creates a novel foundation model
or consciousness.

## Hard constraints
- No purchases, billed APIs, public backend deployment, secret access, or
  merges into main without explicit owner approval.
- Do not download or execute unreviewed model weights or remote code.
- Verify model license and commercial terms **for the exact version** before
  distributing or monetizing.
- Never commit weights, API keys, private user conversations, or training data.
- Prefer local inference and deterministic mock-provider integration tests.
- Keep external-model connection disabled by default until hardware, privacy,
  security, and owner approval gates are satisfied.

## Days 1–30: runnable private inference
1. Inventory actual target hardware (CPU, RAM, GPU/VRAM, OS, free disk).
2. Benchmark candidate small instruct models on the target hardware; record
   model/version, quantization, license, hashes, tokens/s, RAM, latency, and
   failure cases. No unsupported speed promises.
3. Create a provider adapter for a locally bound inference endpoint. Reject
   non-loopback addresses by default, impose input/output limits, and sanitize
   transport errors.
4. Integrate the existing authentication, rate limits, global budget, and
   outstanding-work controls; test timeouts and cancellation.
5. Connect the animated mobile frontend through an approved private backend,
   not through exposed API keys or a public GitHub Pages secret.
6. Test conversation, optional voice, accessibility, and memory consent.

## Days 31–60: Sonny specialization
1. Build opt-in, provenance-tagged memory with user review/delete/export.
2. Establish clean train/eval split; quarantine frozen benchmark material.
3. Create curated synthetic and licensed examples for Sonny's desired behavior.
4. Compare prompting/retrieval versus LoRA adaptation on held-out tasks.
5. Adopt a fine-tune only when measured gains justify compute and maintenance.

## Days 61–90: hardening and release candidate
1. Security review: auth, injection, privacy, abuse, resource exhaustion,
   prompt/response logging, update provenance, and dependency scanning.
2. Measure accuracy, calibration, memory fidelity, latency, and failure rates.
3. Prepare private pilot, rollback, incident response, and operating-cost plan.
4. Commercial launch only after separate deployment and spending approval.

## Acceptance criteria
- Private end-to-end text chat with independently hosted model.
- Measured baseline versus Sonny-customized behavior.
- Explicit consent for memory and no model-data leakage.
- Reproducible tests and documented limitations.
- Security and operational review before any public release.

## Current blockers
- Target HP computer hardware specifications unknown.
- Model and exact license not yet selected.
- No model downloaded, trained, or activated.
- Public Safari demo remains scripted until an approved private backend exists.
