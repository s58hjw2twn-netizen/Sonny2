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

def test_probe_invokes_fixed_docker_arguments_with_fake_cli(tmp_path):
    """Exercise the fixed Docker argv without running a real container or model."""
    import os
    fake = tmp_path / "docker"
    args_file = tmp_path / "args.txt"
    fake.write_text('#!/bin/sh\n'
                    'if [ "$1" = "image" ]; then exit 0; fi\n'
                    'printf "%s\\n" "$@" > "$SONNY_TEST_ARGS"\n'
                    'printf "{}\\n"\n')
    fake.chmod(0o755)
    image = "example.invalid/approved@sha256:" + "a" * 64
    env = os.environ.copy()
    env.update({"PATH": str(tmp_path) + ":" + env.get("PATH", ""),
                "SONNY_VOICE_TRIAL_IMAGE": image,
                "SONNY_TEST_ARGS": str(args_file)})
    result = subprocess.run(["bash", str(SCRIPT), "--probe"],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    args = args_file.read_text().splitlines()
    assert args[:2] == ["run", "--rm"]
    assert args[-2:] == [image, "/probe.py"]
    assert args[args.index("--entrypoint") + 1] == "python"
    assert "--network" in args and args[args.index("--network") + 1] == "none"
    assert "--read-only" in args
    assert "--pull" in args and args[args.index("--pull") + 1] == "never"
    mounts = [args[i + 1] for i, value in enumerate(args[:-1]) if value == "--mount"]
    assert len(mounts) == 1 and mounts[0].endswith(",dst=/probe.py,readonly")

def test_speech_mode_explicitly_denied_with_valid_image_syntax():
    import os
    env = os.environ.copy()
    env["SONNY_VOICE_TRIAL_IMAGE"] = "example.invalid/approved@sha256:" + "a" * 64
    for arguments in (["--speech"], ["--probe", "--speech"], ["--run", "/bin/sh"]):
        result = subprocess.run(["bash", str(SCRIPT), *arguments],
                                env=env, capture_output=True, text=True)
        assert result.returncode == 77
        assert "Speech execution disabled" in result.stderr
