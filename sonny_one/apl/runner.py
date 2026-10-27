"""APL-001 offline evaluator. Requires a dedicated Docker host and trusted image.

This never commits, merges, deploys, installs packages, or calls an LLM.
Only externally supplied experimental patches are evaluated.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import stat
import os
import selectors
import signal
from pathlib import Path

from .policy import append_lineage, sha256_bytes, validate_patch
from .compare import compare

IMAGE_RE = re.compile(r"^[A-Za-z0-9._/-]+@sha256:[a-f0-9]{64}$")
REV_RE = re.compile(r"^[a-f0-9]{40}$")


def bounded_execute(argv, timeout=90, output_limit=4000):
    """POSIX child process with bounded output memory and group timeout cleanup."""
    started = time.monotonic()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    tails = {"stdout": b"", "stderr": b""}
    try:
        with selectors.DefaultSelector() as selector:
            for name in tails:
                stream = getattr(process, name)
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(argv, timeout)
                for key, _ in selector.select(min(remaining, .1)):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if data:
                        tails[key.data] = (tails[key.data] + data)[-output_limit:]
                    else:
                        selector.unregister(key.fileobj)
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(argv, timeout)
            process.wait(timeout=remaining)
        return subprocess.CompletedProcess(argv, process.returncode,
            tails["stdout"].decode("utf-8", errors="replace"),
            tails["stderr"].decode("utf-8", errors="replace"))
    finally:
        # Also terminate descendants retaining output pipes after parent exit.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdout.close()
        process.stderr.close()


def execute(argv, timeout=90):
    if argv[0] == "docker":
        return bounded_execute(argv, timeout)
    return subprocess.run(argv, text=True, capture_output=True,
                          timeout=timeout, check=False)


def docker_test(image, workspace, suite, timeout, *, candidate=False, framework="pytest"):
    if framework not in ("pytest", "unittest"):
        raise ValueError("Unsupported test framework")
    name = "sonny-apl-" + uuid.uuid4().hex
    started = time.monotonic()
    command = [
        "docker", "run", "--rm", "--pull=never", "--name=" + name,
        "--network=none", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--read-only", "--pids-limit=128", "--memory=512m", "--cpus=1",
        "--user=65534:65534", "--tmpfs=/tmp:rw,nosuid,nodev,size=64m",
        "--env=HOME=/tmp", "--env=PYTHONPATH=/src",
        "--env=PYTHONDONTWRITEBYTECODE=1",
        "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "--env=SONNY_APL_EVALUATION=1",
        "--env=SONNY_APL_CANDIDATE_TEST=" + ("1" if candidate else "0"),
        "--volume=" + str(workspace) + ":/src:ro",
        "--volume=" + str(suite) + ":/trusted:ro",
        "--workdir=/src", "--entrypoint=python", image,
        *(["-m", "pytest", "-q", "-p", "no:cacheprovider", "/trusted"]
          if framework == "pytest" else
          ["-m", "unittest", "discover", "-s", "/trusted", "-p", "test*.py"]),
    ]
    try:
        result = execute(command, timeout=timeout)
        return {"exit_code": result.returncode,
                "elapsed_seconds": time.monotonic() - started,
                "stdout_tail": result.stdout[-4000:],
                "stderr_tail": result.stderr[-4000:]}
    except (subprocess.TimeoutExpired, OSError) as exc:
        # Killing the Docker client does not stop its daemon-side container.
        try:
            cleanup = execute(["docker", "rm", "--force", name], timeout=15)
            cleaned = cleanup.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            cleaned = False
        return {"exit_code": -1, "error": type(exc).__name__,
                "cleanup_confirmed": cleaned, "container_name": name,
                "elapsed_seconds": time.monotonic() - started}



def preflight_docker_image(image: str) -> dict:
    """Read-only host check: require an already-present digest-pinned image.

    Never pulls images, starts containers, or treats Docker access as safe by itself.
    """
    if not isinstance(image, str) or not IMAGE_RE.fullmatch(image):
        raise ValueError("A digest-pinned Docker image is required")
    try:
        result = execute(["docker", "image", "inspect", "--format",
                          "{{json .RepoDigests}}", image], timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Docker image preflight unavailable") from exc
    if result.returncode != 0:
        raise RuntimeError("Digest-pinned image is not locally available")
    try:
        digests = json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Docker returned invalid image metadata") from exc
    if not isinstance(digests, list) or image not in digests:
        raise RuntimeError("Local image digest does not match requested image")
    return {"image": image, "locally_verified": True,
            "container_executed": False, "network_used": False}


def suite_fingerprint(directory):
    """Stable digest of suite filenames and file contents."""
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Test suite symlinks are prohibited")
        if path.is_dir():
            continue
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("Test suite special files are prohibited")
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def evaluate(source, revision, patch_file, trusted, heldout, image,
             ledger, timeout=90, *, framework="pytest", require_confidential_holdout=False):
    if framework not in ("pytest", "unittest"):
        raise ValueError("Unsupported test framework")
    if require_confidential_holdout is not False:
        raise RuntimeError("Confidential holdout evaluation is not supported by the candidate-readable test mount")
    if type(timeout) is not int or not 1 <= timeout <= 600:
        raise ValueError("Timeout must be an integer in [1, 600]")
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
    if trusted == heldout or trusted in heldout.parents or heldout in trusted.parents:
        raise ValueError("Trusted and held-out suites must be distinct")
    for suite in (trusted, heldout):
        if suite == source or source in suite.parents or suite in source.parents:
            raise ValueError("Independent test suites cannot live in the source tree")
    # Fail before copying or executing a candidate if the trusted image is absent.
    preflight_docker_image(image)
    trusted_hash = suite_fingerprint(trusted)
    heldout_hash = suite_fingerprint(heldout)
    patch = patch_file.read_text(encoding="utf-8")
    paths = validate_patch(patch)
    candidate_id = sha256_bytes(patch.encode("utf-8"))
    report = {"test_framework": framework, "candidate_id": candidate_id, "base_revision": revision,
              "image": image, "trusted_suite_sha256": trusted_hash,
              "heldout_suite_sha256": heldout_hash,
              "paths": paths, "status": "REJECTED", "promotion": "FORBIDDEN",
              "heldout_confidential_from_candidate": False,
              "heldout_isolation": "read_only_mount_candidate_readable",
              "independent_holdout_custody_verified": False}
    try:
        with tempfile.TemporaryDirectory(prefix="sonny-apl-") as tmp:
            # Apply precisely the validated bytes, not a mutable inbox path.
            validated_patch = Path(tmp) / "validated.diff"
            validated_patch.write_text(patch, encoding="utf-8")
            fixtures = Path(tmp) / "fixtures"
            fixtures.mkdir(mode=0o755)
            trusted_copy, heldout_copy = fixtures / "trusted", fixtures / "heldout"
            for original, snapshot, expected in ((trusted, trusted_copy, trusted_hash),
                                                  (heldout, heldout_copy, heldout_hash)):
                shutil.copytree(original, snapshot, symlinks=True)
                if suite_fingerprint(snapshot) != expected:
                    raise RuntimeError("Test fixtures changed while snapshotting")
                snapshot.chmod(0o755)
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
                               "--check", "--", str(validated_patch)])
            if checked.returncode:
                raise RuntimeError("Patch failed git apply --check")
            applied = execute(["git", "-C", str(workspace), "apply",
                               "--", str(validated_patch)])
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
            baseline = Path(tmp) / "baseline"
            base_clone = execute(["git", "clone", "--no-hardlinks", "--no-checkout",
                                  "--", str(source), str(baseline)])
            if base_clone.returncode:
                raise RuntimeError("Unable to create disposable baseline checkout")
            base_checkout = execute(["git", "-C", str(baseline), "checkout",
                                     "--detach", revision])
            if base_checkout.returncode:
                raise RuntimeError("Base revision not available in baseline")
            shutil.rmtree(baseline / ".git")
            baseline.chmod(0o755)
            shutil.rmtree(workspace / ".git")
            # Docker user 65534 must be able to traverse the disposable checkout.
            Path(tmp).chmod(0o755)
            workspace.chmod(0o755)
            report["baseline_deterministic"] = docker_test(image, baseline, trusted_copy, timeout, **({"framework": framework} if framework != "pytest" else {}))
            report["baseline_heldout"] = docker_test(image, baseline, heldout_copy, timeout, **({"framework": framework} if framework != "pytest" else {}))
            report["deterministic"] = docker_test(image, workspace, trusted_copy, timeout, candidate=True, **({"framework": framework} if framework != "pytest" else {}))
            if report["deterministic"]["exit_code"] == 0:
                report["heldout"] = docker_test(image, workspace, heldout_copy, timeout, candidate=True, **({"framework": framework} if framework != "pytest" else {}))
            if (suite_fingerprint(trusted) != trusted_hash or
                    suite_fingerprint(heldout) != heldout_hash or
                    suite_fingerprint(trusted_copy) != trusted_hash or
                    suite_fingerprint(heldout_copy) != heldout_hash):
                raise RuntimeError("Test fixtures changed during evaluation")
            report["comparison"] = compare(
                {"base_revision": revision,
                 "deterministic": report["baseline_deterministic"],
                 "heldout": report["baseline_heldout"]},
                {"base_revision": revision,
                 "deterministic": report["deterministic"],
                 "heldout": report.get("heldout", {"exit_code": -1, "skipped": True})})
            baseline_ok = (report["baseline_deterministic"]["exit_code"] == 0
                           and report["baseline_heldout"]["exit_code"] == 0)
            candidate_ok = (report["deterministic"]["exit_code"] == 0
                            and report.get("heldout", {}).get("exit_code") == 0)
            report["status"] = ("ELIGIBLE_FOR_HUMAN_REVIEW"
                                if baseline_ok and candidate_ok
                                else "REJECTED")
            if not baseline_ok:
                report["error"] = "Baseline suite failed; comparison is not a valid clean baseline"
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        report["error"] = str(exc)[:500]
    report["lineage_hash"] = append_lineage(Path(ledger), {
        "candidate_id": candidate_id, "base_revision": revision,
        "image": image, "trusted_suite_sha256": trusted_hash,
        "heldout_suite_sha256": heldout_hash,
        "status": report["status"],
        "report_sha256": sha256_bytes(json.dumps(report, sort_keys=True).encode()),
        "baseline_deterministic_exit": report.get("baseline_deterministic", {}).get("exit_code"),
        "baseline_heldout_exit": report.get("baseline_heldout", {}).get("exit_code"),
        "deterministic_exit": report.get("deterministic", {}).get("exit_code"),
        "heldout_exit": report.get("heldout", {}).get("exit_code"),
    })
    return report


def main():
    parser = argparse.ArgumentParser(description="Offline experimental patch evaluator")
    for arg in ("source", "revision", "patch", "trusted", "heldout", "image", "ledger"):
        parser.add_argument("--" + arg, required=True)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--framework", choices=("pytest", "unittest"), default="pytest")
    parser.add_argument("--require-confidential-holdout", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        parser.error("Timeout must be 1–600 seconds")
    print(json.dumps(evaluate(args.source, args.revision, args.patch,
                              args.trusted, args.heldout, args.image,
                              args.ledger, args.timeout, framework=args.framework,
                              require_confidential_holdout=args.require_confidential_holdout), indent=2))


if __name__ == "__main__":
    main()
