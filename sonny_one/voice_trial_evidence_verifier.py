"""Offline verification of trial evidence. Not a sandbox certification."""
import hashlib
import json
from pathlib import Path

EXPECTED = ("probe.json", "assessment.json")

def verify_trial_evidence(folder: Path) -> tuple[bool, tuple[str, ...]]:
    failures = []
    if not isinstance(folder, Path) or folder.is_symlink() or not folder.is_dir():
        return False, ("invalid evidence directory",)
    manifest = folder / "SHA256SUMS"
    if manifest.is_symlink() or not manifest.is_file():
        return False, ("missing checksums",)
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
        hashes = {}
        for line in lines:
            digest, name = line.split(maxsplit=1)
            name = name.lstrip("*")
            if name in hashes or name not in EXPECTED or len(digest) != 64:
                raise ValueError("invalid checksum entry")
            int(digest, 16)
            hashes[name] = digest.lower()
        if set(hashes) != set(EXPECTED):
            raise ValueError("incomplete checksums")
        for name in EXPECTED:
            candidate = folder / name
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError("missing or linked evidence")
            observed = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if observed != hashes[name]:
                raise ValueError("evidence digest mismatch")
        assessment = json.loads((folder / "assessment.json").read_text())
        if not isinstance(assessment, dict):
            raise ValueError("assessment must be a mapping")
        if assessment.get("full_isolation_certified") is not False:
            failures.append("assessment improperly certifies isolation")
        if assessment.get("observation_checks_passed") is not True:
            failures.append("observation checks failed")
        probe = json.loads((folder / "probe.json").read_text())
        if not isinstance(probe, dict):
            raise ValueError("probe must be a mapping")
        from .voice_container_evidence import check_container_observations
        valid, issues = check_container_observations(probe)
        if not valid:
            failures.extend(issues)
        if assessment.get("observation_checks_passed") is not valid:
            failures.append("assessment and independently computed verdict disagree")
        recorded_failures = assessment.get("failures")
        if not isinstance(recorded_failures, list) or tuple(recorded_failures) != tuple(issues):
            failures.append("assessment failure details disagree with observations")
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
    return not failures, tuple(failures)
