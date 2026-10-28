# Sonny ONE private memory: consent and encryption design (research branch)

**Status: design and pure consent-policy prototype only.** No encrypted
persistence, credential store, authentication integration or production rollout
is implemented. Browser localStorage remains unencrypted sample-data storage.

## Trust boundary

1. Authenticate an owner before accessing a memory record. Derive owner identity
   from a verified session, never from a client-supplied owner ID.
2. Require explicit, purpose-specific, time-bounded consent for **save** and
   **recall**. Consent must be independently checked on each action. Owner
   deletion is allowed even after consent expires.
3. Authorize every operation by record owner, including metadata and indexes.
   Do not include cross-user memory in prompts, logs or search results.
4. Encrypt memory at rest using a vetted authenticated-encryption library
   (AES-256-GCM or ChaCha20-Poly1305), fresh unique nonces, and associated
   data binding the owner ID, record ID, schema version and purpose.
5. Keep encryption keys outside the database and repository. Use a documented
   key lifecycle: provisioning, rotation, revocation, recovery and deletion.
   Never reuse a nonce under a key. Do not implement custom cryptography.
6. For deletion, remove records, indexes and derived embeddings; define
   backup retention and deletion guarantees before pilot enrollment. Erasure
   cannot retroactively delete previously exported transcripts.
7. Do not log memory contents, encryption keys, access tokens or decrypted
   prompts. Record minimal consent and deletion audit events without contents.
8. Restrict retention by purpose and expiry; avoid implicit learning from chat.
   Consent withdrawal blocks future save/recall immediately.
9. Test cross-user denial, expired/revoked consent, key failures, tampering,
   restore behavior, migration and backup erasure before private pilot use.

## Current code

`sonny_one/memory_consent_policy.py` is a pure authorization decision
function. It neither authenticates users nor writes or encrypts records.
Its caller must supply trusted identity and expiry. It is not connected to
the public demo routes and does not make those routes private.

## Implementation gate

Before introducing actual storage: choose the local encrypted store and
vetted cryptography dependency; decide owner-controlled key recovery and
consent UX; obtain approval for credentials and access policy changes;
then implement authenticated integration and adversarial tests. No paid
service or production deployment is required for this design phase.
