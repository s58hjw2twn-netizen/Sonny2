# APL-001 Docker evaluation setup (not yet executed)

The APL runner requires a **prebuilt image pinned by SHA-256 digest**.
The Dockerfile is a reproducible template, not a verified image or an
authorization to build, deploy, or purchase resources.

## Prerequisites
- A disposable, nonproduction Docker host.
- A trusted Python base image, specified as `repository@sha256:<digest>`.
- Offline, independently vetted pytest wheels placed in `wheels/`.
- Trusted and held-out test directories outside the candidate source tree.
- A full 40-character immutable Git revision and a policy-compliant patch.
- Explicit owner authorization before running a real container evaluation.

## Build and verify
From this directory, once all prerequisites exist, a human operator can run:

```sh
docker build --network=none \
  --build-arg PYTHON_BASE='python@sha256:<verified-base-digest>' \
  -t sonny-apl-evaluator:local -f Dockerfile .
docker image inspect sonny-apl-evaluator:local --format '{{index .RepoDigests 0}}'
```

If the image has no repository digest, do **not** substitute a mutable tag or
an image ID for the runner's digest requirement. Publish only to a controlled
local registry with digest support, or use a previously audited digest-pinned
image. Do not upload images to an external registry without approval.

The runner invokes `docker run --pull=never --network=none` with read-only
mounts, a read-only root filesystem, resource limits, no Linux capabilities,
and a nonroot user. Test fixtures are mounted at `/trusted` in each run.
The held-out suite is *not* cryptographically secret from candidate code.

## Important limitations
- The image and actual Docker sandbox have **not** been built or tested here.
- Docker CLI flags alone are not proof of host-level containment.
- The current evaluator requires a passing baseline and candidate for review;
  it does not demonstrate improved capability or automatically promote patches.
- Do not use production credentials, personal data, or secrets in test fixtures.
- Preserve the frozen RSI reference and other research baselines.
