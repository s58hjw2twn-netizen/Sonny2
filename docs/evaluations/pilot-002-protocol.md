# Pilot 002 — prospective controlled evaluation plan

**Status: proposed, not activated.** Pilot 001's inconclusive verdict is not retroactively changed.

## Consent, scope, and custody
Obtain Tammy's explicit participation agreement before collecting any new records. Keep private conversation content and identifiers out of GitHub. Use pseudonymous task IDs, minimal metadata and a private access-controlled evidence store with a retention/deletion policy. This repository contains only schema, tests and aggregate analysis code.

## Pre-registered measures
1. **Task completion:** count only independently verified completed outcomes; publish coverage denominator and unknowns.
2. **Factual accuracy:** independent reviewers sample factual claims against dated authoritative sources; track material errors and unverifiable claims.
3. **Verification quality:** record whether supporting sources actually support the claim, including freshness.
4. **Memory continuity:** predefined cross-session preferences with explicit consent; test recall and abstention.
5. **Personalization:** compare task-relevant preferences applied correctly against predefined cases.
6. **Instruction following:** score against the instructions in force for each task.
7. **Error recovery:** preserve original error, correction, follow-up and recurrence test.
8. **Autonomy:** distinguish suggested, prepared, attempted and externally confirmed actions.
9. **Transparency:** audit claims of tool use, execution, verification and uncertainty.
10. **Usefulness:** explicit user feedback, not inferred from continued use.

## Required gates before launch
- Agree on test dates, task sample, independent reviewers and minimum sample sizes.
- Pre-register score definitions, missing-data policy, thresholds and stopping rules.
- Record consent, privacy and access boundaries.
- Validate task ledger schema and tests in CI.
- Conduct a small dry run with synthetic data and inspect the resulting scorecard.

**No pass threshold is selected yet.** The owner and participant must approve it before testing; choosing it after observing results would bias the verdict.

## Engineering references
- `sonny_one/integration/pilot_evaluation.py`: in-memory evidence validation and descriptive scorecard.
- `tests/test_sonny_one_pilot_evaluation.py`: regression checks.
- `docs/evaluations/tammy-pilot-001-intake.md`: historical intake summary.
