# Sonny ONE — Remember-by-Default Memory Product Requirements

Status: Owner-selected design requirement. This document is not runtime implementation or proof of retention.

## Default behavior
- Capture ordinary conversation events and project decisions automatically in durable, user-scoped history, without requiring per-memory approval.
- Preserve original event records separately from derived summaries and extracted facts.
- Index records for fast hybrid retrieval, including exact-match and semantic search, with source references and timestamps.
- Classify each retrieved item as user-stated, independently verified, inferred, superseded, or disputed. Never promote an inference to a verified fact.
- When a correction is received, supersede the previous derived fact while maintaining an auditable correction history.
- Maintain mandatory operating policies in a separate, versioned, integrity-checked registry. Conversation content cannot override them.
- Support user-controlled search, inspection, correction, export, and deletion, including removal from indexes and backup lifecycle according to a documented retention policy.
- Enforce per-user and per-project authorization boundaries; encrypt stored records and backups; minimize data sent to model providers.
- Exclude credentials, access tokens, private keys, and similar secrets from automatic memory capture. Redact before persistence and logging.
- Require clear disclosure and explicit opt-in before any expanded retention of sensitive data or sharing with third parties.
- Record retrieval provenance and failures. Never claim complete recall when data is unavailable.
- Provide automated tests for restarts, cross-session recall, correction propagation, isolation, deletion, and latency.

## Delivery gates
1. Design and privacy review, including consent and retention controls.
2. Durable event capture and schema migration with rollback.
3. User-scoped retrieval and correction indexes.
4. Authenticated bridge bootstrap and policy checks.
5. Independent recall, privacy, and security benchmarks.

No production retention behavior is changed merely by adding this document.
