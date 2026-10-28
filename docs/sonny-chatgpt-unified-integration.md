# Sonny ONE unified ChatGPT integration — implementation checkpoint

Status: **local, read-only prototype only**. Nothing in this document
asserts a deployed endpoint, registered ChatGPT app, authenticated remote
connection, private-memory integration, or autonomous coding.

## Architecture

1. ChatGPT's existing GitHub connector may inspect the repository, subject to
   the user's current connection, permissions and ChatGPT product availability.
   GitHub access is not a persistent Sonny runtime connection.
2. `sonny_one/integration/bridge_contract.py` declares capabilities. All
   capabilities are disabled, including status, memory, patch execution,
   commits, deployments, paid model calls and merges.
3. `status_asgi.py` is an independent ASGI prototype exposing only
   `GET /health` and `GET /v1/public/status`. It is not authenticated and
   MUST NOT be exposed publicly or expanded to private data without security review.
4. `mcp_contract.py` and `mcp_protocol.py` expose a local read-only
   `sonny_public_status` tool. `mcp_stdio.py` offers a local newline-delimited
   JSON-RPC test transport. No network listener, private data, or write tools.
5. The existing development controller remains proposal-only. No model response
   can authorize itself, attest its own sandbox, or grant repository credentials.

## Local verification

From the repository root using the project Python environment:

```sh
python -m unittest discover -s tests -p 'test_sonny_one_bridge_contract.py' -v
python -m unittest discover -s tests -p 'test_sonny_one_status_asgi.py' -v
python -m unittest discover -s tests -p 'test_sonny_one_mcp_contract.py' -v
python -m unittest discover -s tests -p 'test_sonny_one_mcp_protocol.py' -v
python -m unittest discover -s tests -p 'test_sonny_one_mcp_stdio.py' -v
```

CI is configured on `research/unified-chatgpt-bridge` to run the full suite.
Check the run at the exact head commit; earlier green runs do not verify later commits.

## Security gates before remote ChatGPT registration

- Verify a supported ChatGPT custom-app/MCP connection flow for the account.
- Establish independently administered HTTPS hosting, trusted authentication
  and authorization, token audience/scope/expiry validation, rate limits,
  audit logging, and safe handling of secret rotation and revocation.
- Implement a standards-conformant remote MCP transport and complete protocol
  compatibility tests against the actual ChatGPT connection mechanism.
- Keep public status and authenticated personal memory on distinct surfaces;
  require explicit user consent and per-user isolation before reading memory.
- Authenticate controller execution grants cryptographically and bind grants
  to exact task, repository, branch, patch digest, expiry, and one-time nonce.
  Verify signer trust, sandbox attestation and replay protection outside
  candidate-controlled workspaces.
- Prove isolated patch-generation, deterministic tests, held-out tests,
  independent evidence custody, rollback, and restricted GitHub write scope.
- Only then consider staged unattended commits to an isolated research branch.
  Never enable automatic `main` merges, public deployment, or paid usage
  without explicit authorization.

## Operator boundaries

Do not request the owner paste API keys or GitHub tokens into chat.
Do not imply the ChatGPT connection will be permanent: connection persistence
and permissions are controlled by the platform and the account owner.
The current branch is research-only and must not be merged into `main`
without explicit approval.
