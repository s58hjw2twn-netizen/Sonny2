#!/usr/bin/env bash
set -euo pipefail
# Deliberately requires a preloaded, owner-approved digest-pinned image.
# Never pulls images or executes speech models.
image="${SONNY_VOICE_TRIAL_IMAGE:?Set an approved, locally available image@sha256:digest}"
if [[ ! "$image" =~ @sha256:[a-f0-9]{64}$ ]]; then
  echo "Image must be pinned to an approved sha256 digest" >&2
  exit 2
fi
docker image inspect "$image" >/dev/null
out="${SONNY_VOICE_TRIAL_OUTPUT_DIR:-voice-isolation-evidence}"
mkdir -p "$out"
docker run --rm --pull never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 512m --memory-swap 512m \
  --pids-limit 32 --cpus 1 --user 65534:65534 \
  --mount "type=bind,src=$(pwd)/scripts/sonny_voice_isolation_probe.py,dst=/probe.py,readonly" \
  --entrypoint python "$image" /probe.py > "$out/probe.json"
python - "$out/probe.json" "$out/assessment.json" <<'PY'
import json
import sys
from pathlib import Path
from sonny_one.voice_container_evidence import check_container_observations
source, destination = map(Path, sys.argv[1:])
data = json.loads(source.read_text())
passed, failures = check_container_observations(data)
destination.write_text(json.dumps({
    "observation_checks_passed": passed,
    "failures": failures,
    "full_isolation_certified": False,
}, sort_keys=True, indent=2) + "\n")
if not passed:
    raise SystemExit("Container observations failed; inspect evidence")
print("Observed container limits passed; isolation is NOT certified.")
PY
sha256sum "$out/probe.json" "$out/assessment.json" > "$out/SHA256SUMS"
