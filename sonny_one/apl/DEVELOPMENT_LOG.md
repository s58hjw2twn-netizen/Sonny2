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
