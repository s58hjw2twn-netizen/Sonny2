import hashlib
import json
from pathlib import Path
from sonny_one.voice_trial_evidence_verifier import verify_trial_evidence

def fixture(folder):
    folder.mkdir()
    probe = {"isolation_verified": False, "network_default_route_absent": True,
             "memory_max": str(512*1024*1024), "pids_max": "32",
             "cpu_max": "100000 100000", "root_mount": "overlay / overlay ro,relatime 0 0"}
    assessment = {"full_isolation_certified": False, "observation_checks_passed": True, "failures": []}
    (folder / "probe.json").write_text(json.dumps(probe))
    (folder / "assessment.json").write_text(json.dumps(assessment))
    (folder / "image-id.txt").write_text("sha256:" + "a"*64 + "\n")\n    (folder / "image-reference.txt").write_text("example.invalid/approved@sha256:" + "b"*64 + "\n")\n    (folder / "SHA256SUMS").write_text("".join(
        hashlib.sha256((folder / name).read_bytes()).hexdigest() + "  " + name + "\n"
        for name in ("probe.json", "assessment.json", "image-id.txt", "image-reference.txt")
    ))

def test_valid_fixture_is_integrity_consistent(tmp_path):
    folder = tmp_path / "trial"
    fixture(folder)
    assert verify_trial_evidence(folder) == (True, ())

def test_tampered_evidence_rejected(tmp_path):
    folder = tmp_path / "trial"
    fixture(folder)
    (folder / "probe.json").write_text("{}")
    assert not verify_trial_evidence(folder)[0]

def test_missing_manifest_rejected(tmp_path):
    folder = tmp_path / "trial"
    fixture(folder)
    (folder / "SHA256SUMS").unlink()
    assert not verify_trial_evidence(folder)[0]

def test_self_certification_rejected_even_with_updated_hash(tmp_path):
    folder = tmp_path / "trial"
    fixture(folder)
    assessment = folder / "assessment.json"
    assessment.write_text(json.dumps({"full_isolation_certified": True, "observation_checks_passed": True}))
    lines = (folder / "SHA256SUMS").read_text().splitlines()
    lines[1] = hashlib.sha256(assessment.read_bytes()).hexdigest() + "  assessment.json"
    (folder / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    assert not verify_trial_evidence(folder)[0]

def test_forged_assessment_failure_details_rejected(tmp_path):
    folder = tmp_path / "trial"
    fixture(folder)
    assessment = folder / "assessment.json"
    assessment.write_text(json.dumps({
        "full_isolation_certified": False,
        "observation_checks_passed": True,
        "failures": ["fabricated"],
    }))
    lines = (folder / "SHA256SUMS").read_text().splitlines()
    lines[1] = hashlib.sha256(assessment.read_bytes()).hexdigest() + "  assessment.json"
    (folder / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    assert not verify_trial_evidence(folder)[0]

def test_missing_failure_list_rejected(tmp_path):
    folder = tmp_path / "trial"
    fixture(folder)
    assessment = folder / "assessment.json"
    assessment.write_text(json.dumps({
        "full_isolation_certified": False, "observation_checks_passed": True
    }))
    lines = (folder / "SHA256SUMS").read_text().splitlines()
    lines[1] = hashlib.sha256(assessment.read_bytes()).hexdigest() + "  assessment.json"
    (folder / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    assert not verify_trial_evidence(folder)[0]
