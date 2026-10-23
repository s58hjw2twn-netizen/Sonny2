# Sonny ONE private Safari hosting preparation

Status: planning only. No public deployment or billable services authorized.

## Existing boundary
The local authenticated pilot is deliberately loopback-only. Do not change its network boundary or reuse its local signing configuration for internet exposure.

## Required implementation
1. Create a separate hosted application entry point and production configuration. Keep the local pilot unchanged.
2. Enforce HTTPS, canonical host and Origin validation, secure session cookies, CSRF protections, account-specific authorization, login throttling, session revocation, and secure secret management.
3. Add persistent encrypted-at-rest storage and a documented backup, retention and deletion policy. Verify Railway volume and restart behavior before deployment.
4. Provide explicit memory consent, corrections, deletion, and portability controls. Never import real user data into a test deployment.
5. Add a model adapter with explicit provider authorization and verifiable spending controls. Until then show that responses are demo-only.
6. Test Safari on real iPhone over cellular, mobile viewport and keyboard behavior, reconnects, logout, cookies, home-screen install, and failures.
7. Add automated negative security tests for spoofed Host/Origin, remote-client behavior, session expiry, cross-account access, and storage failures.
8. Perform independent security review before any private internet-facing pilot.

## Railway preparation checklist
- Inspect current project/service status and pricing without restarting anything.
- Identify required environment variables by name only; do not create or expose secrets in a public repository.
- Prepare a private deployment plan and rollback instructions.
- Estimate hosting and model usage cost before asking owner to approve deployment.
- Never deploy, alter security-sensitive settings, purchase services, or merge to main without separate explicit approval.

## Release acceptance
Private Safari URL works over cellular with HTTPS; real AI is connected only under approved provider/budget; consented memory persists across devices and restarts; isolation and security checks pass. Current status: not yet met.
