# RES-001 fixture custody and baseline expectations

The two fixture directories in this tree are **templates only**. The APL
runner rejects trusted or held-out suites inside its source repository.
For an experiment, copy them to **separate, operator-controlled directories
outside the source tree**. Do not point the APL runner directly at these
in-repository templates.

- Trusted template:
  `sonny_one/development_controller/fixtures/res001_trusted/`
- Held-out template:
  `sonny_one/development_controller/fixtures/res001_heldout/`

The current research target intentionally has a failing baseline for empty
sequences: `mean([])` raises `ZeroDivisionError`. The proposed improvement
should make that case raise `ValueError`. A baseline failure on that
specific new requirement is **expected**; other unexpected baseline failures
are not.

Before running the APL evaluator:

1. Freeze and fingerprint both external fixture directories.
2. Record the exact 40-character baseline revision and digest-pinned Docker
   image. Use an independently controlled Docker host.
3. Confirm the patch applies cleanly and the model proposal passed static
   checks. Never execute generated code outside the APL sandbox.
4. Run the trusted and held-out suites with the APL evaluator against
   baseline and candidate workspaces.
5. Review the APL report, regression outcomes, and hash-linked lineage.
   Neither a passing test nor a static check authorizes promotion to main.

The held-out template is committed to this repository and therefore is
**not secret from a model with repository access**. For rigorous research,
use an independently maintained held-out suite that the model and its
development prompt cannot read. These fixtures are useful for functional
regression checks, not proof of generalizable RSI.

No live-model evaluation has yet been recorded.
