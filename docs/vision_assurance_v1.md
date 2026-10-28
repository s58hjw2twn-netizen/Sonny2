# Sonny Vision / Sonny ONE assurance v1

Research-only. Not production-certified and not autonomous self-improvement.

## Hard constraints
Create an explicit unique list of required checks before execution. Missing
evidence fails closed. For a localized photograph edit, include at minimum:
pixel containment, identity preservation, historical reference accuracy,
insignia orientation, and customer approval. A pixel validator alone proves
only pixel containment, not historical or identity correctness.

## Independent verification
Use `evaluate(constraints, evidence, creator=...)`. Each check must have
a named verifier different from the creator and a traceable reference.
These names and references are assertions, not cryptographic proof of
independence; deployment must use separate trusted execution identities,
evidence custody, and access controls. Do not auto-approve a photograph.

## Failure learning
`FailureLedger` stores append-only hash-linked failure records.
`choose_method` excludes a method after two recorded failures for the same
task type and escalates if no alternative remains. A hash chain detects
accidental changes, but cannot prevent full-file rewrite by an attacker;
production requires externally anchored hashes and controlled append access.
Never store source photos or sensitive personal data in the ledger.

## Validation
Run `python -m unittest discover -s tests -p 'test_vision_*.py'`
in an isolated development environment with Pillow installed.
Do not merge or deploy before review and CI verification.
