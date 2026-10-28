"""Read-only APL host readiness check; never runs candidate containers.

A PASS here permits planning containment tests, not trusting hostile code.
"""
import argparse
import json
import re
import shutil
import subprocess

PINNED_IMAGE = re.compile(r"^[A-Za-z0-9._/-]+@sha256:[a-f0-9]{64}$")


def check_host(image=None, *, which=shutil.which, run=subprocess.run):
    checks = []
    def record(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    docker = which("docker")
    record("docker_cli", docker is not None, "Docker CLI found" if docker else "Docker CLI unavailable")
    pinned = isinstance(image, str) and bool(PINNED_IMAGE.fullmatch(image))
    record("pinned_image_reference", pinned,
           "Digest-pinned reference" if pinned else "A locally vetted name@sha256:64 lowercase hex reference is required")
    if docker:
        for name, args in (
            ("daemon", [docker, "info", "--format", "{{.ServerVersion}}"]),
            ("rootless", [docker, "info", "--format", "{{json .SecurityOptions}}"]),
        ):
            try:
                completed = run(args, capture_output=True, text=True, timeout=8, check=False)
                if name == "daemon":
                    record(name, completed.returncode == 0,
                           "Daemon reachable" if completed.returncode == 0 else "Daemon unavailable")
                else:
                    options = json.loads(completed.stdout) if completed.returncode == 0 else []
                    if not isinstance(options, list):
                        options = []
                    rootless = any(isinstance(x, str) and x.lower() in ("name=rootless", "rootless") for x in options)
                    record(name, rootless, "Rootless indicated" if rootless else "Rootless not verified")
            except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
                record(name, False, "Probe unavailable")
        if pinned:
            try:
                result = run([docker, "image", "inspect", image, "--format", "{{json .RepoDigests}}"],
                             capture_output=True, text=True, timeout=8, check=False)
                digests = json.loads(result.stdout) if result.returncode == 0 else []
                verified = isinstance(digests, list) and image in digests
                record("local_image", verified,
                       "Matching local digest" if verified else "Image/digest not verified locally")
            except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
                record("local_image", False, "Image inspection unavailable")
    return {"ready_for_containment_validation": all(c["passed"] for c in checks),
            "hostile_code_execution_approved": False,
            "checks": checks,
            "note": "This probe runs no containers. Independent isolation and cleanup tests are mandatory."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", help="Locally vetted digest-pinned image reference")
    args = parser.parse_args()
    report = check_host(args.image)
    print(json.dumps(report, indent=2))
    return 0 if report["ready_for_containment_validation"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
