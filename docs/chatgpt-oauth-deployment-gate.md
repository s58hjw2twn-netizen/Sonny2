# Sonny ONE ChatGPT OAuth connection — deployment gate

Status: **NOT DEPLOYED; NOT CONNECTED**. This document is a pre-deployment
security checklist, not permission to expose the local MCP prototype.

## Verified in research CI (user-confirmed green)
- Local Streamable HTTP initialize, tools/list, and tools/call
- RS256 token validation with issuer, audience, expiration and scope
- Protected ASGI initialization, tool listing, and status-tool execution
- Rejection of unauthenticated and insufficient-scope requests

## Required before public HTTPS exposure
1. Choose a trusted OAuth 2.1 authorization server supporting Authorization Code
   with PKCE and an appropriate client-registration strategy for ChatGPT.
2. Implement resource-server discovery metadata at
   `/.well-known/oauth-protected-resource` (and path-specific variant if needed).
   Advertise the exact HTTPS resource identifier and authorization server.
3. Configure the authorization server's metadata, authorization endpoint,
   token endpoint, supported PKCE methods and registration approach. Never
   invent these URLs or implement a fake OAuth flow.
4. Validate JWT access tokens against a trusted, rotating JWKS, with fixed
   accepted algorithms, issuer, resource audience, expiration and scope.
   Existing pinned-PEM RS256 validation is only a local research prototype.
5. Require TLS and enforce strict host/origin controls, CORS policy,
   resource identifiers, least-privilege scopes, rate limits and audit logging
   without token or secret disclosure.
6. Test OAuth discovery, PKCE login, token exchange, expiration, wrong
   issuer/audience/scope, key rotation, tool access, and reconnect/revocation.
7. Perform independent security review and explicitly approve a limited
   private deployment. Do not expose local-only port 8766 or use an open tunnel.
8. Verify the actual ChatGPT custom MCP connection with a read-only tool
   before considering any GitHub write permissions.

## Required deployment inputs (not yet selected)
- Trusted OAuth provider and tenant / issuer URL
- Private deployment host and HTTPS domain
- Client registration policy and redirect URI requirements
- Secret storage and key rotation strategy
- Account authorization / pilot user allowlist

No purchases, public deployment, production secrets, or main-branch changes
are authorized by this document.
