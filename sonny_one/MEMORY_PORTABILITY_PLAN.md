# Memory portability

Goal: keep approved memories independent of the selected model.

Requirements:
- Versioned JSON format.
- Per-user export of active consented records only.
- Explicit user approval before import.
- Validate all entries before writing.
- Atomic import with rollback on failure.
- Tests for user isolation, revocation, and malformed input.

No model API calls or deployment are required for this design.
