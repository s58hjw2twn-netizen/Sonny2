"""Static safeguards for the diagnostic-only sandbox executor."""
from pathlib import Path
import subprocess

SCRIPT = Path("scripts/sonny_voice_sandbox_executor.sh")

def test_speech_execution_denied_without_docker():
    result = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 77

def test_probe_requires_explicit_digest_pinned_image():
    result = subprocess.run(["bash", str(SCRIPT), "--probe"], capture_output=True, text=True,
                            env={"PATH": "/usr/bin:/bin", "SONNY_VOICE_TRIAL_IMAGE": "python:latest"})
    assert result.returncode == 77

def test_fixed_docker_restrictions_and_no_arbitrary_execution():
    script = SCRIPT.read_text()
    for required in ("--pull never", "--network none", "--read-only",
                     "--cap-drop ALL", "no-new-privileges", "--memory 512m",
                     "--pids-limit 32", "--cpus 1", "--user 65534:65534",
                     "dst=/probe.py,readonly", "--entrypoint python",
                     '"$image" /probe.py'):
        assert required in script
    assert 'if [[ "${1:-}" != "--probe" || "$#" -ne 1 ]]' in script
    assert "docker pull" not in script
