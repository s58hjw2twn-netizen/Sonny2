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
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"
out="${SONNY_VOICE_TRIAL_OUTPUT_DIR:-voice-isolation-evidence}"
# Never mix a new run with existing evidence or overwrite an earlier trial.
if [[ -e "$out" || -L "$out" ]]; then
  echo "Evidence destination already exists; supply a fresh directory" >&2
  exit 2
fi
mkdir -- "$out"
# Capture the exact inspected image identity alongside probe observations.
docker image inspect "$image" --format '{{.Id}}' > "$out/image-id.txt"
printf '%s\\n' "$image" > "$out/image-reference.txt"
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
print("Observed checks:", "PASS" if passed else "FAIL", "; isolation is NOT certified.")
PY
(cd "$out" && sha256sum probe.json assessment.json image-id.txt image-reference.txt > SHA256SUMS)
python - "$out/assessment.json" <<'PY'
import json
import sys
from pathlib import Path
result = json.loads(Path(sys.argv[1]).read_text())
if not result["observation_checks_passed"]:
    raise SystemExit("Container observations failed; retained hashed evidence")
PY
