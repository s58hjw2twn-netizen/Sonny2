#!/usr/bin/env bash
set -euo pipefail
# A separate, sandbox-owned execution entry point. No host model execution.
# Disabled until model provenance and per-run authorization are independently enforced.
echo "Sonny speech sandbox execution is disabled pending verified model provenance and authorization" >&2
exit 77
