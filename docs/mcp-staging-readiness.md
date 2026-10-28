# Sonny ONE MCP staging readiness

Status: NOT DEPLOYED. Keep the existing production service unchanged.

- Use a separate staging service and a dedicated container build.
- Install the MCP SDK and cryptography dependencies independently of the existing app.
- Bind the staging process to Railway's assigned port only after OAuth and security gates are met.
- Require a trusted OAuth issuer, validated audience, scoped tokens, and public resource metadata.
- Keep write-capable tools disabled; verify read-only protocol_status first.
- Do not expose the local loopback prototype as a public service.
- Verify CI, lifecycle, authentication rejection, and a real client handshake before promoting.
