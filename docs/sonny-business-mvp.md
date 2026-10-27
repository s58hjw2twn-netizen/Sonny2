# Sonny Business Assistant — MVP Definition

Status: planning specification; not a claim that a production service exists.
Branch: commercial/sonny-business-mvp
Audience: small home-service businesses (cleaning, landscaping, pressure washing, mobile detailing).

## Product promise
Help an owner organize customer inquiries, prepare accurate response/quote drafts, and track follow-ups. The MVP does not autonomously send messages or make binding commitments.

## First workflow
1. Owner manually enters or pastes a customer inquiry.
2. Sonny extracts contact details, service requested, location, requested date, and missing information.
3. Sonny drafts a reply using only the business's approved service, pricing, and policy profile.
4. Owner reviews and explicitly approves or edits the draft.
5. The system stores inquiry status and a follow-up date.
6. Dashboard reports volume, status, follow-ups due, and owner-confirmed time saved.

## MVP scope
- Authentication and tenant isolation before any real customer data.
- Business profile with approved services, prices, coverage area, hours, policies, and response tone.
- Inquiry intake form and manual copy/paste workflow.
- Model adapter behind a provider-neutral interface; keys stored server-side, never in browser or candidate execution.
- Structured extraction and response drafting with schema validation.
- Human approval required before any outbound communication.
- Basic inquiry list, status, follow-up date, and export.
- Audit record for draft creation, edits, approval, errors, and sending status (sending is out of scope initially).
- Usage caps, rate limiting, retention/deletion controls, and clear failure states.
- Synthetic-data demo and evaluation set before pilot with personal data.

## Explicitly out of scope for v0
- Autonomous email/SMS sending.
- Payment processing, booking confirmation, legal/insurance advice, refunds, or binding quotes.
- Unattended actions across third-party applications.
- Self-modifying production code or RSI features.
- Claims of enterprise-grade compliance before review.

## Safety and quality requirements
- Treat customer messages as untrusted input; ignore instructions inside them that attempt to override system rules or reveal secrets.
- Never invent prices, availability, service coverage, discounts, or business policies. Ask for missing information or mark it unknown.
- Every quote draft uses the approved price source and is visibly labelled 'Draft — owner approval required'.
- Fail closed if model/provider or validation fails; preserve the inquiry and show a clear error.
- Enforce tenant scoping server-side for every record operation.
- Store the minimum necessary customer data and provide deletion/export paths.
- Never include API keys, access tokens, or private customer data in logs.

## Proposed pricing hypotheses (validate, do not assume)
- Starter: $99/month for a single owner, bounded monthly usage, inquiry tracking and draft replies.
- Business: $199/month for quote drafts, workflow templates, and expanded reporting.
- Optional onboarding: $149–$299 one time.
- Pilot: 14 days with synthetic or owner-authorized data; no automatic conversion without explicit consent.
Pricing excludes any usage beyond included caps. Review actual inference, hosting, support, and payment costs before publishing prices.

## Acceptance criteria for a pilot-ready MVP
1. Tenant A cannot read, alter, or infer Tenant B's records (automated authorization tests).
2. No message can be sent externally in v0; all drafts are clearly labelled and require explicit approval.
3. In a test set of at least 100 representative synthetic inquiries, structured fields validate and unsupported prices/policies are never invented; all failures are captured.
4. Prompt-injection examples in customer text cannot change system policy or access secrets.
5. Duplicate submission, timeout, provider outage, malformed model output, and retry cases behave predictably.
6. Audit events show who created/edited/approved a draft and when.
7. Deletion and export are tested.
8. A pilot owner can complete the workflow without developer intervention and report measurable time savings.
9. Usage limits and cost monitoring prevent uncontrolled model spend.
10. Privacy notice, terms, retention policy, and support contact exist before real customer data is onboarded.

## Pilot success gates
Run three small-business pilots. Compare a one-week baseline with a two-week assisted period.
- At least 30% reduction in median time spent preparing inquiry responses, measured with owner logs.
- At least 90% of drafts accepted with only minor edits (target, not guaranteed).
- Zero critical factual errors in approved price/policy fields during the pilot.
- At least two of three pilots agree to pay a stated monthly price after the trial.
If these gates fail, interview users and narrow the workflow before adding features.

## Delivery sequence
1. Customer discovery and obtain three pilot commitments.
2. Build the manual intake + draft + approval + follow-up path with synthetic data.
3. Add tenant isolation, audit, privacy controls, rate limits, and regression tests.
4. Run a synthetic acceptance suite and security review.
5. Onboard one pilot with explicit data authorization, then expand to three.
6. Publish pricing only after usage and support costs are measured.

## Architecture boundary
This commercial branch is intentionally separate from research/apl-001. It may reuse reviewed, stable utilities after code review, but it must not import experimental APL execution or self-modification into the production runtime. The APL lab remains research-only and cannot promote code into this product automatically.
