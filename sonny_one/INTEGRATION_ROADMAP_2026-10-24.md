# Sonny ONE — Six-capability integration checkpoint

Date: 2026-10-24. Branch: `research/apl-001`.

## Priority order
1. Personal Memory
2. Integrity & Self-Checking
3. Voice & Personality
4. Sonny Vision
5. Personal Agent
6. Creative Studio

## Repository observations
- Memory admission, storage, retrieval, erasure and import/export modules exist.
- Assistant and model-router modules exist, but do not establish a connected production model.
- Sonny Vision geometry and face-region modules exist, but no operational restoration pipeline is verified.
- No integrated voice runtime, general external-action executor or creative media runtime was verified in this inspection.
- Existing development status documentation includes historical test results; these do not establish current-commit CI success.

## Changes in this checkpoint
- `sonny_one/capability_inventory.py`: conservative, static six-module inventory with fail-closed external-execution decisions.
- `tests/test_sonny_one_capability_inventory.py`: five unit tests.

## Next work
1. Execute current branch tests and review CI results; resolve failures before claiming verification.
2. Introduce runtime-sourced evidence records (actual tool permissions, enabled providers, and action receipts) rather than using this static inventory as a live capability indicator.
3. Add explicit per-user consent and memory provenance checks at every integration boundary.
4. Integrate image compositing only after face protection and reference-fidelity tests pass.
5. Prototype voice and creative tools behind opt-in, license-audited adapters.
6. Design personal-agent action confirmation, isolation, and audit logs before enabling any external effects.

No main merge, deployment, paid calls, or frozen benchmark changes authorized.
