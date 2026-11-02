#!/usr/bin/env bash
set -euo pipefail
# Sandbox-owned diagnostic entry point. No speech engine or arbitrary command execution.
# Speech execution remains blocked until model provenance and authorization are enforced.
if [[ "${1:-}" != "--probe" || "$#" -ne 1 ]]; then
  echo "Speech execution disabled; only --probe is supported" >&2
  exit 77
fi
image="${SONNY_VOICE_TRIAL_IMAGE:-}"
if [[ ! "$image" =~ ^[a-zA-Z0-9._/-]+@sha256:[a-f0-9]{64}$ ]]; then
  echo "Locally cached, digest-pinned image required" >&2
  exit 77
fi
command -v docker >/dev/null || { echo "Docker unavailable" >&2; exit 77; }
docker image inspect "$image" >/dev/null || { echo "Image not cached" >&2; exit 77; }
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
probe="$root/scripts/sonny_voice_isolation_probe.py"
[[ -f "$probe" && ! -L "$probe" ]] || exit 77
# Fixed read-only mount; no caller-supplied command, image pull, or writable volume.
exec docker run --rm --pull never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 512m --memory-swap 512m \
  --pids-limit 32 --cpus 1 --user 65534:65534 \
  --mount "type=bind,src=$probe,dst=/probe.py,readonly" \
  --entrypoint python "$image" /probe.py
