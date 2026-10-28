# Sonny ONE: permanent failure-prevention requirements

Research branch only. These controls must be integrated with actual tool adapters,
CI, trusted verification and approval services before production use.

## Additional lessons from the USMC collar failure

1. **Repeated prompts are not a corrective mechanism.** Stop a method after
   repeated evidence-backed failures. Do not silently retry a blocked method.
2. **Preservation must be enforced by the execution layer.** A prompt saying
   "do not touch faces" is not a substitute for source hashes, edit masks,
   file allowlists and post-edit pixel checks.
3. **Correct-looking output can be historically wrong.** Evidence provenance
   is necessary but not sufficient: a qualified reviewer must inspect the
   exact period-specific source and actual result.
4. **Independent verification needs separate authority.** A different string
   for the verifier is not proof of independence. Production verifiers need
   separate credentials, immutable evidence custody and no candidate-code
   access to hidden tests.
5. **Customer approval must be tied to an exact artifact hash.** A generic
   approval flag is not enough: bind approval to the verified output digest,
   request version and customer identity in an authenticated service.
6. **Tests must measure real outcomes.** Unit tests using synthetic pixels
   cannot prove that 1987 Marine Corps collar devices are correctly oriented.
   Add a licensed/authorized fixture and a documented expert review.
7. **A change in code is not a measured improvement.** Run baseline and
   candidate against identical frozen cases with isolated execution,
   non-regression thresholds and independent audit records.
8. **Failure records are not immutable merely because hashes are linked.**
   Anchor the ledger externally, restrict writes, and protect against
   concurrent writers and truncation.
9. **Do not overclaim security or permanence.** Changes lower specific risks
   only after tests and deployment enforcement. No software is hacker-proof.

## Release blockers

- Run and fix all tests in isolated CI.
- Integrate ChangePlan with the real image editor and GitHub patch executor.
- Use a canonical path resolver to prevent path traversal, symlinks and
  ambiguous file aliases in production.
- Establish independently authenticated reviewer identities and evidence.
- Pin benchmark manifests and score definitions to immutable hashes.
- Add transactional, tamper-evident ledger storage and retention policies.
- Bind customer approval to the output SHA-256, never an unverified draft.
- Prove real-image collar correction with all other pixels unchanged.
- Verify historical correctness against actual 1987-era official sources.

## Validation

Run `python -m unittest discover -s tests -p 'test_vision_*.py'`.
A passing test run is necessary but not sufficient for commercial release.
