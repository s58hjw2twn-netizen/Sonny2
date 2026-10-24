# APL-001 development log — 2026-10-24

## Starting evidence

- Branch: `research/apl-001`; verified starting HEAD:
  `b13e84af71c75ae49c57c343d0b295c84856fd6d`.
- Connected GitHub workflow API returned no runs for this SHA or `4d014cc`;
  combined commit status returned no statuses. A fallback direct Actions API
  read subsequently verified run `40100974177` for `b13e84a` completed SUCCESS
  (2026-10-24 14:05:57 UTC). The specialized connector result was incomplete.
- Starting APL unittest suite: 47 passed; syntax compilation passed.
- Initial whole-suite unittest discovery: 109 discovered, 5 import errors
  because pytest/FastAPI/PyJWT were unavailable. This was an environment issue,
  not a verified code regression. Unittest also does not collect pytest functions.

## Implemented and verified locally

- Named Docker containers with explicit forced removal after client timeout or
  OS failure. Report cleanup confirmation and elapsed time; force Python
  entrypoint so a trusted image's default entrypoint cannot alter invocation.
- Snapshot validated patch text before Git application; reject overlapping test
  suite directories, invalid API timeouts and special fixture files.
- Recheck fixture fingerprints after the paired experiment; reject drift.
- Bind complete pre-lineage report contents into the ledger via SHA-256.
- Do not classify pytest collection/usage/internal errors, no-tests exit,
  Docker errors or timeouts as functional repairs/regressions.
- Bounded supplied-proposal queue with duplicate rejection, preregistered
  predictions, hard candidate budget and infrastructure stop behavior.
- Seeded task-paired bootstrap interval, explicitly conditional on task
  independence and provided scores; never marks improvement proven.
- Enable existing full-suite workflow for the research branch.
- Offline image template now requires a fully pinned, hash-checked dependency
  lock. No lock or audited image is invented or bundled.

Validation before commit:

- `python -m compileall -q sonny_one/apl tests`: PASS.
- `python -m unittest discover -s tests -p 'test_apl_*.py' -q`: 56 PASS.
- Temporary venv, installed repository `requirements.txt` using free package
  downloads; `python -m pytest -q`: **175 passed**, 1 upstream Starlette/AnyIO
  deprecation warning, 5.90 seconds. No production environment modified.
- Five existing browser JavaScript syntax checks: PASS.
- `git diff --check`: PASS.
- Git clone/apply orchestration tests use real temporary Git repositories;
  **all Docker execution in these tests is mocked**.

## Security and interpretation limits

This was a focused source audit, not a penetration test or independent review.
Candidate code can read its mounted held-out tests and can tamper with its own
in-process Python execution. Exit zero is not independent proof of correctness.
Fingerprint pre/post checks detect persistent drift, not malicious change-and-
restore races; host suite directories must be protected from concurrent writers.
The ledger serializes cooperating POSIX writers, but requires independent
backups: it is unsigned,
not externally anchored, and not safe against a privileged attacker rewriting
history. Grader identifiers are unauthenticated assertions. Bootstrap estimates
cannot correct benchmark leakage, task dependence or grader bias. Container
output capture is bounded to the final 4,000 bytes per stream. A failed Docker
cleanup needs operator action. POSIX locking/process controls require Linux;
Windows execution is not supported by these research runner components.
No claim of safe hostile-code execution is made.

## Blockers and next-action queue

1. Provision an already-free disposable Docker host: this environment has
   neither a Docker executable nor `/var/run/docker.sock`. Do not run candidates
   directly on the host as a substitute.
2. Validate host containment and timeout cleanup with real containers.
   Host-side output bounds, cooperating-writer locks and private fixture
   snapshots were implemented in the second hardening pass.
3. Independently acquire/vet a pinned base image, wheel lock and image digest;
   test offline build and inspect runtime restrictions on that host.
4. Obtain independently authored private task fixtures and grader evidence with
   access controls; current tests are public orchestration fixtures.
5. Run repeated real baseline/candidate experiments with preregistered tasks,
   independent grading, uncertainty and reproducibility measurements.
6. Audit any model-backed proposal generation separately. Current loop accepts
   supplied proposals only; no paid model calls or recursive promotion exist.
7. Human owner reviews any promotion. Nothing merges or deploys automatically.

No measured functional gain, generalization, consciousness or recursive
self-improvement was established. Frozen baselines and production code remain
unchanged. Commit and remote verification outcomes are recorded below after
publication to the authorized research branch.

## Second hardening pass

- Bound Docker client output to 4,000 bytes per stream using incremental pipe
  reads; kill timed-out process groups. Real subprocess flood and timeout tests
  passed without Docker.
- Serialize lineage appends with POSIX advisory locks; forty concurrent writes
  preserve a valid chain. Malformed JSON/records fail verification cleanly.
- Copy fixture trees into private experiment storage, verify snapshot digests,
  and use the same snapshots for baseline and candidate. Mounts remain read-only.
- Final local suite: **179 passed**, 1 upstream deprecation warning, 5.97 seconds.
  APL coverage increases from 47 to 60 tests. No real Docker experiments run.
- Local first-pass commit: `92834fa`. Shell push failed for lack of credentials;
  publish the final tested tree through the connected GitHub Git-data API.

## Published verification

- Published implementation commit:
  `a5c5b0f08848bc78b22f0e9a7e8d4fe0f99ee7f6` on `research/apl-001`.
- Remote tree `b6b2bc313c8bff23d72d047ad2437355cb0289b4` exactly matches the
  locally tested tree (verified by Git tree SHA and empty tree diff).
- GitHub APL checks: run `40101331018`, **SUCCESS**.
- GitHub full Sonny ONE tests: run `40101331039`, job `120893913413`,
  **SUCCESS**, including dependency installation, deterministic tests and all
  browser JavaScript syntax checks.
- The connected specialized commit-runs endpoint returned empty results;
  direct Actions REST reads through the same connector supplied actual evidence.
- Local checkpoint commits `92834fa` and `caea5c1` were consolidated into the
  single published implementation commit. No untested source differences.
- This final log update is documentation only; its own commit identifier is
  available in repository history, avoiding a self-referential commit hash.

Authorized implementation has reached the next empirical gate. Remaining
scientific validation needs a real, vetted sandbox and independently controlled
fixtures/grading. No new purchase, deployment, promotion, or frozen-baseline
change was made. Current evidence supports tested engineering safeguards, not
validated containment or a functional intelligence gain.


## Continuation checkpoint — 2026-10-24

- Verified branch head `30556f30c252ff7050b0812757a31b510150dfcc` with successful APL policy checks (40101634158) and full Sonny ONE checks (40101634185).
- Corrected fail-open Docker preflight: a missing image reference previously allowed a mock rootless daemon to pass readiness; invalid image-inspection results also needed defensive parsing. Fix: `43d20e97890dedb5a2ed2730ca6ff7d5a76f10c7`.
- Added tests for omitted pinned image and malformed inspection response; focused APL remote checks passed (40101749179). The full-suite run 40101749198 was pending during this entry; verify it before claiming success.
- Host readiness is **not** authorization to execute untrusted code; preflight never runs Docker containers. Docker behavior is mocked in these unit tests.

### Ordered remaining empirical gates

1. Provide an independently vetted disposable Linux/rootless Docker host and locally cached audited digest-pinned image. Confirm build reproducibility and offline dependencies.
2. Run real container containment, networking, resource ceiling, timeout and cleanup tests on that host; inspect residual processes and mounted files.
3. Independently source protected final-test fixtures and grader records that patch authors cannot choose or access before evaluation.
4. Repeatedly run paired clean-baseline versus candidate tasks, record repair/regression deltas, uncertainty, and repeatability; avoid reusing final holdouts for optimization.
5. Inspect results for tampering, benchmark contamination, and security problems, and require explicit owner approval before any promotion.

Unverified: real hostile-code containment, task improvement, generalization, consciousness and recursive self-improvement. No production merge, public deployment, paid API charge or frozen-baseline modification.


## Continuation — rootless preflight security audit (2026-10-24)

- Research branch before change: `47d3290`; both APL and full-suite CI workflows succeeded.
- Found a false-positive readiness path: substring matching accepted misleading Docker security options such as `name=not-rootless`. Changed detection to accept only exact recognized tokens (`name=rootless` or `rootless`).
- Added negative regression cases for misleading strings and non-string JSON security-option entries.
- Code commit: `5dbfeb3278e566839a648ed28dba914a23f4e3c2`.
- GitHub remote verification: APL policy checks run `40101935669` SUCCESS; full Sonny ONE tests run `40101935664` SUCCESS.
- These are unit/mock and standard CI results. They do not establish a real rootless daemon, pinned runtime, containment, or any candidate functional improvement.

Next blocker remains a disposable audited Linux Docker host, vetted hash-pinned offline image, and independent private test/grader custody. Avoid candidate execution against a host not independently confirmed. No production promotion or deployment.


## Continuation — immutable proposal intake (2026-10-24)

- Prior research security fix `5dbfeb3` and log update `320eda7` both verified by full and APL GitHub CI.
- Audited `loop.run_queue`: validated patch files were reopened by evaluator after intake, introducing an inbox time-of-check/time-of-use gap. The post-execution candidate hash guard detected mismatches too late.
- Commit `c2e5947e8fdc40c37440c2d426c19af8a97a2b0b` now passes an isolated temporary snapshot of the originally validated patch text to the evaluator. The preregistered digest is tied to that content. Added a regression test that mutates the inbox during evaluation.
- GitHub APL checks `40102033993`: SUCCESS. Full Sonny ONE tests `40102034108`: SUCCESS.
- This protects against ordinary mutable-input races, not malicious host compromise or candidate process escape. Docker remains mocked for orchestration unit tests.
- Remaining empirical blockers: rootless disposable Docker host, independently audited pinned image/dependencies, container escape/resource tests, protected independent holdouts/grader, and repeated real baseline/candidate experiments. No measurable functional improvement or genuine RSI established.
