"""APL-001 offline evaluator. Requires a dedicated Docker host and trusted image.

This never commits, merges, deploys, installs packages, or calls an LLM.
Only externally supplied experimental patches are evaluated.
"""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .policy import append_lineage, sha256_bytes, validate_patch

IMAGE_RE = re.compile(r"^[A-Za-z0-9._/-]+@sha256:[a-f0-9]{64}$")
REV_RE = re.compile(r"^[a-f0-9]{40}$")


def execute(argv, timeout=90):
    return subprocess.run(argv, text=True, capture_output=True,
                          timeout=timeout, check=False)


def docker_test(image, workspace, suite, timeout):
    command = [
        "docker", "run", "--rm", "--pull=never",
        "--network=none", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--read-only", "--pids-limit=128", "--memory=512m", "--cpus=1",
        "--user=65534:65534", "--tmpfs=/tmp:rw,nosuid,nodev,size=64m",
        "--env=HOME=/tmp", "--env=PYTHONPATH=/src",
        "--env=PYTHONDONTWRITEBYTECODE=1",
        "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "--volume=" + str(workspace) + ":/src:ro",
        "--volume=" + str(suite) + ":/trusted:ro",
        "--workdir=/src", image,
        "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "/trusted",
    ]
    try:
        result = execute(command, timeout=timeout)
        return {"exit_code": result.returncode,
                "stdout_tail": result.stdout[-4000:],
                "stderr_tail": result.stderr[-4000:]}
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"exit_code": -1, "error": type(exc).__name__}


def evaluate(source, revision, patch_file, trusted, heldout, image,
             ledger, timeout=90):
    source = Path(source).resolve(strict=True)
    trusted = Path(trusted).resolve(strict=True)
    heldout = Path(heldout).resolve(strict=True)
    patch_file = Path(patch_file).resolve(strict=True)
    if not REV_RE.fullmatch(revision):
        raise ValueError("A full 40-character immutable Git commit SHA is required")
    if not IMAGE_RE.fullmatch(image):
        raise ValueError("A prebuilt, digest-pinned Docker image is required")
    if not source.is_dir() or not trusted.is_dir() or not heldout.is_dir():
        raise ValueError("Source and independent test suites must be directories")
    if trusted == heldout:
        raise ValueError("Trusted and held-out suites must be distinct")
    for suite in (trusted, heldout):
        if suite == source or source in suite.parents:
            raise ValueError("Independent test suites cannot live in the source tree")
    patch = patch_file.read_text(encoding="utf-8")
    paths = validate_patch(patch)
    candidate_id = sha256_bytes(patch.encode("utf-8"))
    report = {"candidate_id": candidate_id, "base_revision": revision,
              "paths": paths, "status": "REJECTED", "promotion": "FORBIDDEN"}
    try:
        with tempfile.TemporaryDirectory(prefix="sonny-apl-") as tmp:
            workspace = Path(tmp) / "workspace"
            clone = execute(["git", "clone", "--no-hardlinks", "--no-checkout",
                             "--", str(source), str(workspace)])
            if clone.returncode:
                raise RuntimeError("Unable to create disposable local checkout")
            checkout = execute(["git", "-C", str(workspace), "checkout",
                                "--detach", revision])
            if checkout.returncode:
                raise RuntimeError("Base revision not available in source")
            checked = execute(["git", "-C", str(workspace), "apply",
                               "--check", "--", str(patch_file)])
            if checked.returncode:
                raise RuntimeError("Patch failed git apply --check")
            applied = execute(["git", "-C", str(workspace), "apply",
                               "--", str(patch_file)])
            if applied.returncode:
                raise RuntimeError("Patch could not be applied")
            changed = execute(["git", "-C", str(workspace), "status",
                               "--porcelain", "-z"])
            if changed.returncode:
                raise RuntimeError("Cannot inspect changed paths")
            actual = set()
            for entry in changed.stdout.split("\0"):
                if not entry:
                    continue
                actual.add(entry[3:])
            if actual != set(paths):
                raise RuntimeError("Changed file set differs from approved patch")
            shutil.rmtree(workspace / ".git")
            # Docker user 65534 must be able to traverse the disposable checkout.
            Path(tmp).chmod(0o755)
            workspace.chmod(0o755)
            report["deterministic"] = docker_test(image, workspace, trusted, timeout)
            if report["deterministic"]["exit_code"] == 0:
                report["heldout"] = docker_test(image, workspace, heldout, timeout)
            report["status"] = ("ELIGIBLE_FOR_HUMAN_REVIEW"
                                if report["deterministic"]["exit_code"] == 0
                                and report.get("heldout", {}).get("exit_code") == 0
                                else "REJECTED")
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        report["error"] = str(exc)[:500]
    report["lineage_hash"] = append_lineage(Path(ledger), {
        "candidate_id": candidate_id, "base_revision": revision,
        "status": report["status"],
        "deterministic_exit": report.get("deterministic", {}).get("exit_code"),
        "heldout_exit": report.get("heldout", {}).get("exit_code"),
    })
    return report


def main():
    parser = argparse.ArgumentParser(description="Offline experimental patch evaluator")
    for arg in ("source", "revision", "patch", "trusted", "heldout", "image", "ledger"):
        parser.add_argument("--" + arg, required=True)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        parser.error("Timeout must be 1–600 seconds")
    print(json.dumps(evaluate(args.source, args.revision, args.patch,
                              args.trusted, args.heldout, args.image,
                              args.ledger, args.timeout), indent=2))


if __name__ == "__main__":
    main()
