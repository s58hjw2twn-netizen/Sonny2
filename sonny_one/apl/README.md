# Sonny ONE Autonomous Patch Laboratory (APL-001) — experimental

Status: **research scaffold, not validated RSI or production software**.
Branch: `research/apl-001`, based on `feature/sonny-one-foundation`.
Never alter frozen SEB-1.0, CSAT-1.3 or RSI v1.3. Never promote automatically.

## What exists

- `policy.py`: deny-by-default diff scope restricted to
  `sonny_one/apl_targets/`, patch size/type checks, SHA-256-linked JSONL
  lineage records and integrity verifier.
- `runner.py`: accepts an **external proposed patch** and exact base commit,
  applies it to a disposable local checkout, and runs two independent test
  suites using a prebuilt digest-pinned Docker image. Tests are mounted
  read-only from directories **outside** the candidate source tree. No
  network, root filesystem writes, Linux capabilities, or privileged user.
- `tests/test_apl_policy.py`: proposed unit tests for scope, traversal,
  symlinks, renames, duplicates, patch size and lineage tampering.

This is a **proposal intake and evaluation prototype**, not an autonomous
proposal generator. No LLM, model training, recursive iteration, background
execution, promotion, production connection, or deployment is implemented.

## Evaluation command (on a dedicated disposable runner)

```bash
python -m pytest -q tests/test_apl_policy.py
python -m sonny_one.apl.runner \
  --source /trusted/Sonny2 \
  --revision FULL_40_CHARACTER_GIT_SHA \
  --patch /inbox/candidate.diff \
  --trusted /private/trusted-tests \
  --heldout /private/heldout-tests \
  --image sonny-apl-runner@sha256:REPLACE_WITH_REAL_64_HEX_DIGEST \
  --ledger /private/apl/lineage.jsonl
```

The trusted runner image must be built and audited independently with Python,
pytest and required dependencies installed; its actual SHA-256 digest must be
supplied. Neither test directory may be inside the source tree. Candidate
generation must not see held-out cases. However, because pytest and candidate
code run inside the same container, a malicious candidate can inspect the
mounted test files at evaluation time. Read-only mounts protect integrity, not
confidentiality. Treat held-out scores as one signal, require static inspection
and independent review, and never claim cryptographically secret evaluation. Do not run Docker against sensitive
host volumes, secrets, or a privileged Docker socket accessible to candidates.

The runner returns `ELIGIBLE_FOR_HUMAN_REVIEW` only when both test processes
exit zero. This **does not** authorize promotion or establish generalization.
Results must also pass independent review for test manipulation, overfitting,
regressions, security and actual functional improvement. A hash-linked local
ledger detects ordinary accidental edits but is not tamper-proof against a
privileged attacker: replicate signed logs to independent storage before
consequential use.

## Next engineering work

1. Build a dedicated non-production Docker test image and inspect its digest.
2. Create immutable external trusted and held-out test fixtures, with separate
   owners/access controls and contamination checks.
3. Add adversarial integration tests for malformed diffs, test tampering,
   sandbox escape attempts, timeouts, reward hacking and lineage corruption.
4. Add candidate generator that **only emits a diff and prediction** into an
   inbox. Start with one human-proposed candidate and no paid model calls.
5. Add paired baseline-versus-candidate measurements (accuracy, regressions,
   wall-clock time, cost), an independent grader and explicit rejection gates.
6. Require a separately signed owner authorization for **any** merge,
   deployment, API spend, or transfer into commercial Sonny Assistant.

## Research guidance and evidence levels (reviewed 2026-10-23)

- **Empirical preprint:** Darwin Gödel Machine, arXiv:2505.22954. Archive
  multiple candidate lineages and measure edits on coding benchmarks.
  Its results do not demonstrate sentience or unlimited self-improvement.
- **Empirical preprint (Oct 10, 2026):** *Does Failure Feedback Direct Agent Self-Modification?*, arXiv:2610.14662. Reports that selected improvements may not repair the targeted failure or generalize. Track target repair, related-task transfer, and held-out net change separately.
- **Empirical preprint:** Mendel Gödel Machine, arXiv:2608.07645 (Aug 2026).
  Compare trajectories across tasks and lineages; defer cross-lineage
  hybridization until independent baselines exist.
- **Research article:** MUSE, Neural Networks 194 (Feb 2026), 108131.
  Competence awareness and strategy selection suggest logging a candidate's
  predicted pass rate versus actual held-out performance.
- **Empirical benchmark/preprint:** EvilGenie, arXiv:2511.21654, and
  reward-hacking research arXiv:2609.28614. Held-out tests alone are not
  enough: inspect code changes, evaluation process and tampering attempts.
- **Theory / contested:** Butlin et al., arXiv:2308.08708, identify
  theory-dependent consciousness indicators. Seth (2025) and Schneider
  (2026) challenge simplistic computational/behavioral inferences.
  Self-model accuracy and calibration can be evaluated as engineering
  properties; neither is proof of subjective experience.
- **Speculative:** Active-inference and second-order self-model theories
  offer research hypotheses but no verified route to conscious Sonny ONE.

## Release boundary

This experiment is separate from commercial `sonny/app.py` and from frozen
research artifacts. Even a perfect local test result remains experimental.
The owner must explicitly approve any production promotion.
