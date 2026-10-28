# Sonny ONE — Free AI connection gate

Status: **NOT CONNECTED**. The public Safari demo remains scripted. The Gemini request builder, response parser and HTTPS transport are dormant backend components, not a deployed inference service.

## Non-negotiable activation requirements

1. Keep the API key exclusively in a server-side secret store. Never embed it in GitHub Pages, HTML, JavaScript, Git history, logs, or client storage.
2. Explicitly select a free-tier eligible Google AI project and verify current model quotas and billing behavior in the provider console. Do not assume an API request is free because a model has a free tier. No auto-upgrade to a paid tier.
3. Require authenticated requests and a per-user rate limit, a global request limit, and a hard concurrency bound before connecting the transport.
4. Limit input/output sizes and request durations. A Python thread timeout does **not** cancel an in-flight HTTPS request; enforce transport-level deadlines and bound surviving requests.
5. Reject unsupported provider responses and sanitize errors. Avoid logging prompt text or credentials.
6. Use a private staging endpoint for integration tests first; do not deploy publicly without explicit owner approval.
7. Test against mocked provider responses, failure paths, quotas, concurrent requests, and browser connectivity before accepting live inference.
8. Keep frozen research benchmarks isolated. Never substitute live inference into a benchmark condition without a preregistered protocol.

## Current code

- `gemini_request.py`: validates user message and limits output tokens.
- `gemini_response.py`: validates provider responses.
- `gemini_transport.py`: dormant server-side HTTPS transport with a response-size cap.
- `inference_config.py`: fail-closed; external inference still disallowed.
- `safari_demo/index.html`: static scripted prototype with no credential or inference connection.

## Next integration step

Implement an explicitly opt-in private backend adapter that applies the existing authentication, local per-user throttling, and concurrency controls to Gemini transport. Add deterministic tests for quota exhaustion, transport failure, timeout and unauthorized access. Activation and deployment are separate decisions.
