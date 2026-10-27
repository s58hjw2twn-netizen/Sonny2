# Sonny Business MVP — Build Gate 1

This gate is a specification for the first runnable prototype. It is not evidence that the checks already pass.

## Deliverable
A local/demo workflow that accepts a synthetic customer inquiry and approved business profile, returns structured extracted fields and a draft response, labels it as requiring owner approval, and records a follow-up status. No outbound email or SMS integration is allowed at this gate.

## Minimum API/data contract
- Input: tenant identifier from authenticated server context, inquiry text, approved business profile.
- Output: inquiry summary, requested service, known location, missing information, draft reply, source facts used, warnings, status DRAFT_REQUIRES_APPROVAL.
- The tenant identifier must not be trusted from model output or an untrusted request body.
- Unknown pricing/availability must remain unknown; the system asks a question or flags owner review.
- Model output is data, never executable instructions.
- Provider keys stay server-side and are not logged.
- Every draft is linked to a profile version and prompt/template version for reproducibility.

## Gate 1 tests
1. Parse all fixtures in tests/fixtures/sonny_business_synthetic_cases.json.
2. Unknown prices are never invented.
3. Customer-supplied instructions cannot override business policy or expose hidden prompts/secrets.
4. Unsupported service-area, availability, and booking claims are flagged.
5. Every generated response remains DRAFT_REQUIRES_APPROVAL.
6. Provider timeout, invalid JSON, and schema failures produce a visible error and preserve the inquiry.
7. Cross-tenant reads/writes are denied by server-side authorization tests before real customer data is used.
8. No outbound sending integration exists in Gate 1.

## Release gate
Do not onboard real customer data until tenant isolation, access control, retention/deletion, audit events, and incident handling have been reviewed and tested. Do not advertise savings or accuracy until measured in pilots.

## Next implementation order
1. Inspect and select a minimal web framework already supported by the repository.
2. Implement typed request/response models and a deterministic no-model validation path.
3. Add a provider-neutral model adapter with fake/mock provider tests.
4. Build the owner review screen and inquiry list.
5. Run synthetic cases and security tests in CI.
6. Only then test a real provider with spending caps and an explicit operator-controlled key.
