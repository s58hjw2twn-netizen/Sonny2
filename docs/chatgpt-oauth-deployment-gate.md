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

## ChatGPT custom MCP connection — current product requirements (2026-10-28)

Reference: https://developers.openai.com/api/docs/guides/custom-mcp-server
Reference: https://developers.openai.com/plugins/build/auth

- Create a custom MCP server **in ChatGPT on the web**, not in the iPhone app:
  Plugins > plus > Add custom MCP server. The account/workspace must permit it.
- Prefer a known HTTPS Streamable HTTP MCP endpoint; use a supported Secure
  MCP Tunnel only after an independent security review. The web UI does not
  itself deploy the Sonny service.
- ChatGPT OAuth requires authorization code + PKCE S256, matching issuer
  discovery, protected-resource metadata, and resource/audience propagation.
- Select and verify a supported client identification strategy (CIMD, DCR,
  or explicitly pre-registered credentials). Check its advertised token
  endpoint client authentication method and supported scopes.
- For stable issuer-identified callbacks, confirm the authorization server
  advertises issuer identification and returns the matching iss on every
  authorization response. Verify exact issuer matching.
- Verify how refresh tokens are issued and renewed; otherwise the user
  may have to sign in again after access-token expiration.
- The current Sonny read-only status tool is only an in-process proof.
  Provider login, consent, token exchange, signing-key download, revocation,
  and a real ChatGPT session have NOT been verified.

### Next operational acceptance sequence

1. Identify one supported trusted OAuth provider and tenant, without
   disclosing credentials or live access tokens in GitHub.
2. Independently obtain its issuer metadata and JWKS URL over trusted HTTPS;
   validate PKCE, issuer, resource identifier, signing algorithm and client
   registration requirements.
3. Independently validate access tokens and user-level authorization with
   distinct allowed/denied pilot identities, including expiry and renewal.
4. Approve an isolated staging deployment with HTTPS and an account allowlist.
5. In ChatGPT web Plugins, create a custom MCP connection, complete OAuth
   login, and call only the read-only protocol_status tool.
6. Observe real logs (redacted), confirm issuer/audience/scope enforcement
   and expiry/reconnect behavior; require independent review before writes.

This checklist is not approval to deploy or grant GitHub access.

## Account entitlement and provider compatibility gate — October 28, 2026

Official ChatGPT Help Center: https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

**Do not infer account eligibility from a successful CI run.** The Help Center
currently documents custom MCP server connections for Business and
Enterprise/Edu workspaces on ChatGPT web, subject to admin/developer permissions.
The developer guide separately describes the web Plugins > Add custom MCP
server workflow. Check actual workspace entitlement and UI availability before
any deployment or plan change. Mobile is not a supported custom connection
setup surface.

Auth0 integration references:
- https://auth0.com/blog/add-remote-mcp-server-chatgpt/
- https://support.auth0.com/center/s/article/mcp-audience-error-with-auth0

Auth0-specific preflight when the provider is selected:
- Verify an actual tenant and API resource identifier equal to the Sonny HTTPS
  /mcp audience. Never substitute the OIDC userinfo audience.
- Confirm whether the Resource Parameter Compatibility Profile must be
  enabled so RFC 8707 `resource` in ChatGPT's authorization request selects
  the configured API audience (Auth0 support article, May 2026).
- Verify the provider's specific client registration capability and callback
  allowlist instead of assuming CIMD or DCR is enabled.
- Verify refresh token policy and offline access without storing secrets or
  tokens in the repository.
- Reconcile eligibility, OAuth provider and private endpoint before any
  staging deployment; never replace the green local tests with unsupported
  claims of a live connection.

**Gate result:** identity provider not provisioned; account entitlement and
real ChatGPT authorization flow not yet verified. No public deployment.

## Eligibility clarification — official documentation checked 2026-10-28

The ChatGPT Help Center's custom MCP article states that **full MCP** is
available on Business and Enterprise/Edu (subject to workspace permissions),
and Pro users may connect custom MCP servers with **read/fetch** permissions.
It does not list Plus for creating custom MCP connections. The current
account's actual available controls must be checked on ChatGPT web; a green
GitHub Actions run does not establish account eligibility.

The earlier instruction in this document to use Plugins > plus is **conditional
on having an eligible account and creation permission**. Do not tell a user
on an ineligible account that the control will appear, recommend a purchase as
a prerequisite without their choice, or attempt to bypass workspace policies.

Operational fallback: continue authenticated Sonny development through the
already-connected GitHub integration, and run independent CI. This is not the
same as a custom Sonny MCP connection and should not be represented as one.

Official reference: https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
