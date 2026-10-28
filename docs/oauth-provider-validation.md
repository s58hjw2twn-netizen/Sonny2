# OAuth provider acceptance checks

Before enabling staging, independently confirm the selected provider has HTTPS issuer metadata, a matching issuer identifier, an HTTPS authorization endpoint, an HTTPS token endpoint, Authorization Code support, and PKCE S256 support.

Confirm the provider's client registration method, redirect URI rules, access-token audience, required scope, signing-key rotation, and revocation behavior. Reject mismatches; do not infer capabilities from an advertised brand.

No provider has been selected or verified yet. Do not enable the staging listener or change the existing production service.
