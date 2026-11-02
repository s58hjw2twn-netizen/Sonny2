#!/usr/bin/env bash
set -euo pipefail
# No model binaries or network downloads. Uses the Python image already available on runner.
image="${SONNY_VOICE_TRIAL_IMAGE:-python:3.12-slim}"
docker image inspect "$image" >/dev/null
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 512m --memory-swap 512m \
  --pids-limit 32 --cpus 1 --user 65534:65534 \
  --mount "type=bind,src=$(pwd)/scripts/sonny_voice_isolation_probe.py,dst=/probe.py,readonly" \
  --entrypoint python "$image" /probe.py > voice-isolation-probe.json
python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("voice-isolation-probe.json").read_text())
assert data["isolation_verified"] is False
assert data["network_default_route_absent"] is True
assert data["memory_max"] == str(512 * 1024 * 1024), data
assert data["pids_max"] == "32", data
assert data["cpu_max"].split()[0] != "max", data
assert data["root_mount"] and "ro" in data["root_mount"].split()[3].split(","), data
print("Container limits observed; full isolation not certified.")
PY
