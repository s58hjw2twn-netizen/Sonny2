# Sonny ONE next-action queue

Updated 2026-10-16 UTC. Follow LOW_TOUCH_DEVELOPMENT.md. All work stays on
`feature/sonny-one-foundation` until an explicit owner-approved merge.

| Priority | Action | State / dependency |
| --- | --- | --- |
| 1 | Verify new branch commit in GitHub CI | Run after each update; fix failures without interrupting owner |
| 2 | Implement local authenticated backend and server-approved memory | Reviewable defaults in AUTHENTICATED_BACKEND_PLAN.md; owner approval needed for login/access policy and signing configuration |
| 3 | Connect UI to authenticated workspace | After backend isolation, consent, persistence and revocation checks pass |
| 4 | Run Safari/WebKit and Windows browser checks | Chromium checks pass; WebKit system dependencies unavailable in current container; physical devices remain unverified |
| 5 | Certify iPhone home-screen installation | Manifest/offline shell implemented; needs approved device-access plan, no public deployment assumed |
| 6 | Add licensed model integration and hard cost enforcement | Separate owner approval for provider/API charges; no model calls currently enabled |
| 7 | Private pilot | After auth/privacy acceptance; owner approves test users and any personal data |

## Completed this continuation

- Restored a usable local Chromium runner through its download mirror.
- Verified chat and memory flows at 1440, 768, 390 and 320 pixel widths.
- Fixed in-flight draft deletion and invalid saved-record handling.
- Added intent word matching, empty-conversation feedback and reply status.
- Added manifest, icon and offline shell with no user-data/API caching.
- Added a self-contained local browser-check runner and expanded regression cases.
- Prepared backend schema/endpoint/access-policy decisions for owner review.

## Approval request scope

Approve the local test-account authentication/session policy and signing
configuration described in AUTHENTICATED_BACKEND_PLAN.md. This does not authorize
paid services, model API calls, connecting private accounts, main merges, public
hosting or changing frozen benchmarks.
