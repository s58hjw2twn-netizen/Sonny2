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

The evaluator supports bounded processing of externally supplied patch proposals
using `loop.py`. It records predicted pass probabilities before each evaluation,
uses the same baseline for every candidate, and stops on infrastructure errors.
It does not generate model-written patches, train models, promote candidates,
or demonstrate recursive self-improvement.

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

## Bounded proposal queue

Supply a JSON array of objects with exactly `patch` (local diff path) and
`predicted_pass` (probability from 0 to 1). Run:

```bash
python -m sonny_one.apl.loop --manifest /inbox/proposals.json --max-candidates 3 \
  --source /trusted/Sonny2 --revision FULL_40_CHARACTER_GIT_SHA \
  --trusted /private/trusted-tests --heldout /private/heldout-tests \
  --image runner@sha256:REAL_64_HEX_DIGEST --ledger /private/apl/lineage.jsonl
```

The hard budget is ten candidates; per-suite timeouts are 1–600 seconds.
All manifest entries are validated before evaluation. Duplicate patches and
invalid probabilities are rejected. There is no winner selection or promotion.
Predictions describe review eligibility, not probability of scientific improvement.
The queue does not feed held-out answers to a generator. Reusing a held-out suite
across candidate selection can still contaminate it; reserve a separate final
suite under an independent owner.

`metrics.paired_uncertainty` provides a seeded paired task bootstrap with a
computation budget. Its interval assumes representative independent tasks;
it does not establish independence, generalization or repeat-run stability.
External grader names are metadata, not authenticated identities.

## Next engineering work

See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for verified results, audit limits,
infrastructure blockers, and the ordered next-action queue.

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

## Repeated-cycle evidence gate (experimental)

`review_gate.assess_candidate` compares independently supplied paired scores
with the recorded evaluation identity and locally verified lineage.
`cycles.assess_cycles` requires at least three separately identified cycles,
unique candidate IDs, and distinct SHA-256 suite fingerprints. A positive
recommendation requires every cycle to exceed the configured improvement
threshold with a positive task-bootstrap lower bound. Both interfaces are
read-only and always forbid automatic promotion.

**Important:** A fingerprint is an identifier, not proof of independent suite
custody or statistical independence. These functions do not perform actual
self-modification, validate the grader's identity, establish genuine RSI,
or make deployment decisions. Independent review and unseen final evaluation
remain mandatory. Run checks with `python -m unittest discover -s tests -p 'test_apl_*.py'`.

## Offline evidence custody (experimental)

`custody.seal_evidence` creates a canonical JSON SHA-256 evidence envelope
with HMAC-SHA256 authentication under an independently held 32-byte-or-longer
secret. `custody.verify_evidence` rejects altered records, wrong custodians,
and invalid MACs. The key must **never** enter candidate containers, GitHub
source, or public logs. This mechanism is not a digital signature or public
proof of independent evaluation: anyone holding the shared secret can forge
an envelope. Record custody, secure key distribution and independent evaluator
identity remain external operational requirements. No real key is stored here.
