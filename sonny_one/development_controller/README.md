# Sonny ONE Development Controller v1

This is the **completed safe task-planning controller**, not an unattended
AI coding agent. It is designed to minimize repeated chat prompts while
preserving owner approval and independent testing.

## Files
- `tasks.json`: versioned two-track task queue.
- `controller.py`: schema validation, priority selection and approval gates.
- `tests/test_sonny_one_development_controller.py`: fail-closed regression tests.
- `.github/workflows/sonny-development-controller.yml`: read-only GitHub
  Actions validation and downloadable `development-plan.json` artifact.

## Usage
From the repository root:

```sh
python -m sonny_one.development_controller.controller
python -m unittest discover -s tests -p 'test_sonny_one_development_controller.py' -v
```

The workflow triggers on changes to the controller files on
`research/apl-001`. A manual workflow dispatch may require GitHub to
recognize the workflow on the default branch. GitHub's scheduled workflows
also require a default-branch workflow; this research-only branch does not
provide unattended cron execution.

## Not yet available
- Unattended generation, debugging or commits of new code.
- A connected autonomous coding runner with tightly scoped GitHub credentials.
- Scheduled execution independent of commits on the research branch.
- Automatic resolution of security-sensitive or approval-required tasks.

Those require a separately approved, security-reviewed runner integration.
No provider credentials, paid inference or public deployment are enabled.
A queue entry is not evidence that its task has been executed.

## Owner approval boundaries
No paid services, production deployment, secret creation, private account
access, frozen research modification, or merge into main without explicit
approval. Code generation must operate in an isolated branch, use least-
privilege credentials, and pass CI before human review. Do not bypass these
requirements to enable background work.
