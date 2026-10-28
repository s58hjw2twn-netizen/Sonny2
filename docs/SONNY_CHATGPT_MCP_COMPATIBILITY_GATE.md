# ChatGPT MCP compatibility gate — 2026-10-28

**Priority:** Owner priority 1, real ChatGPT connection.

**Evidence:** The local MCP syntax repair at commit `f696aad9597ffa26b1ef0e5e8ad3b873eeffd3bd` passed GitHub Actions run 40737884671. This does NOT establish remote compatibility.

## Current implementation (inspected)

- `sonny_one/integration/private_mcp_asgi.py` is an in-process POST-only `/private/mcp` JSON-RPC prototype.
- It requires a static bearer token, rejects every Origin header, and does not implement production remote MCP transport or user OAuth.
- `mcp_protocol.py` offers initialize, ping, tools/list and read-only tools/call; its implementation is deliberately limited.
- No live hosted Sonny endpoint or registered ChatGPT plugin is verified.

## Official integration requirements and gaps

OpenAI's custom MCP server guidance (reviewed 2026-10-28):
- https://developers.openai.com/api/docs/guides/custom-mcp-server
- https://developers.openai.com/plugins/build/mcp-server
- https://developers.openai.com/plugins/build/auth
- https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

ChatGPT custom plugins support remote streaming HTTP or SSE and require a reachable HTTPS endpoint or supported Secure MCP Tunnel. Auth configuration is OAuth, no auth, or mixed OAuth/no auth. A private authenticated user-facing integration requires an OAuth-compatible authorization architecture; the prototype static bearer token is not a production substitute. Actual plugin creation depends on the account/workspace's permissions and is performed by an authorized user on ChatGPT web.

## Required milestones (do not mark complete without evidence)

1. Choose the permitted connection mode for the owner's ChatGPT account/workspace; do not assume custom MCP creation is enabled.
2. Build standards-conformant streamable HTTP with correct negotiation, lifecycle, errors, and security checks; verify with an independent MCP Inspector/client.
3. Design OAuth 2.1 and per-user access controls for private tools; do not paste credentials into chat or commit them.
4. Set up an owner-controlled HTTPS service or supported secure tunnel with monitoring and revocation.
5. Register/install the custom MCP plugin on ChatGPT web using authorized account controls.
6. Run a real ChatGPT-initiated read-only Sonny tool call and record time, exact tool, expected result, observed result and server-side evidence.
7. Keep autonomous GitHub write tools disabled until the separate independently verified coding runner milestone.

**Blocking question:** Whether the owner's ChatGPT account/workspace permits creating custom MCP plugins. If unavailable, the current plan cannot claim a direct ChatGPT custom plugin connection. Consider a separately operated Sonny client using the OpenAI API only with explicit owner approval and an independently evaluated security/cost plan.

**Safety:** Do not deploy the current private_mcp_asgi prototype as-is. A successful local test is not production security or interoperability.
