"""Execute experimental performance probes only in a restricted Docker container.

The host writes input source files but never imports or executes candidate code.
Results remain descriptive and cannot authorize promotion.
"""
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from .runner import IMAGE_RE, bounded_execute


def benchmark_in_docker(image, baseline_source, candidate_source, benchmark_script,
                        *, timeout=90):
    if not isinstance(image, str) or not IMAGE_RE.fullmatch(image):
        raise ValueError("Digest-pinned Docker image required")
    if not isinstance(baseline_source, str) or not isinstance(candidate_source, str):
        raise ValueError("Source text required")
    if not 1 <= timeout <= 600:
        raise ValueError("Timeout must be between 1 and 600 seconds")
    script = Path(benchmark_script)
    if not script.is_file() or script.is_symlink():
        raise ValueError("Trusted benchmark script required")
    with tempfile.TemporaryDirectory(prefix="apl-benchmark-") as tmp:
        workspace = Path(tmp)
        workspace.chmod(0o755)
        for filename, source in (("baseline.py", baseline_source),
                                 ("candidate.py", candidate_source),
                                 ("benchmark.py", script.read_text(encoding="utf-8"))):
            dest = workspace / filename
            dest.write_text(source, encoding="utf-8")
            dest.chmod(0o644)
        name = "sonny-apl-perf-" + uuid.uuid4().hex
        command = [
            "docker", "run", "--rm", "--pull=never", "--name=" + name,
            "--network=none", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--read-only",
            "--pids-limit=64", "--memory=256m", "--cpus=1",
            "--user=65534:65534", "--tmpfs=/tmp:rw,nosuid,nodev,size=16m",
            "--env=HOME=/tmp", "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=PYTHONNOUSERSITE=1",
            "--volume=" + str(workspace) + ":/bench:ro",
            "--workdir=/bench", "--entrypoint=python", image,
            "-I", "-B", "/bench/benchmark.py",
        ]
        try:
            result = bounded_execute(command, timeout=timeout, output_limit=65536)
        except (subprocess.TimeoutExpired, OSError) as exc:
            # Killing the client does not guarantee daemon-side cleanup.
            try:
                cleanup = bounded_execute(
                    ["docker", "rm", "--force", name], timeout=15)
                confirmed = (cleanup.returncode == 0 or
                             "No such container" in cleanup.stderr)
            except (subprocess.TimeoutExpired, OSError):
                confirmed = False
            if not confirmed:
                raise RuntimeError(
                    "Benchmark failed; daemon-side container cleanup unconfirmed") from exc
            raise RuntimeError("Isolated benchmark timed out or unavailable") from exc
        if result.returncode != 0:
            raise RuntimeError("Isolated benchmark failed: " + result.stderr[-500:])
        try:
            report = json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("Benchmark returned invalid JSON") from exc
        if not isinstance(report, dict) or report.get("promotion_allowed") is not False:
            raise RuntimeError("Benchmark report missing non-promotion boundary")
        return report
