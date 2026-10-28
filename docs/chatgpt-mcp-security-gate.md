# Sonny ONE ChatGPT MCP connection — security gate (draft)

Status: design only; no deployed MCP endpoint or successful ChatGPT handshake verified.

## Existing application
- The research branch uses FastAPI in `sonny/app.py` and an application-specific HS256 JWT session verifier.
- The Dockerfile starts `uvicorn sonny.app:app`.
- Existing app bearer sessions must **not** be treated as OAuth authorization for ChatGPT.

## Required implementation gates
1. Implement a standards-compliant Streamable HTTP MCP endpoint using a pinned, reviewed MCP SDK. Do not publish a placeholder endpoint.
2. Add OAuth-compatible resource authorization with issuer, audience, expiration, and scope validation. Reject missing/invalid tokens before tool dispatch. Do not accept `x-user-id` as identity.
3. Initially expose only an innocuous read-only status tool that returns static build metadata, no secrets, private records, GitHub contents, or environment variables.
4. Restrict CORS/Origin and host handling to explicitly configured trusted origins/hosts; enforce HTTPS at deployment and bounded request sizes/timeouts.
5. Keep GitHub writes, shell execution, arbitrary URL fetches, secrets, and autonomous code changes completely unavailable through the initial MCP endpoint.
6. Add negative tests for unauthenticated, expired, wrong-audience, wrong-scope, and forged identity requests; positive tests for MCP initialize, tools/list and read-only tools/call.
7. Verify locally and through CI; then inspect the deployed HTTPS endpoint independently. Record URL only after verified. Test connection from ChatGPT without entering credentials in chat.
8. Any future coding-to-commit capability requires a separate isolated executor, least-privilege credentials, approval boundaries, independent tests, and audit records. Never merge to main automatically.

## Release criteria
No user-facing claim of an active Sonny ONE MCP connection until authenticated ChatGPT initialization and a read-only tool call both succeed against the deployed endpoint.
