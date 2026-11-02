from pathlib import Path

def test_trial_requires_approved_digest_and_no_pull():
    script = Path("scripts/sonny_voice_container_trial.sh").read_text()
    assert "SONNY_VOICE_TRIAL_IMAGE:?" in script
    assert "@sha256:" in script
    assert "--pull never" in script
    assert "--network none" in script
    assert "--read-only" in script
    assert "--cap-drop ALL" in script
    assert "--security-opt no-new-privileges" in script

def test_trial_emits_evidence_but_never_self_certifies():
    script = Path("scripts/sonny_voice_container_trial.sh").read_text()
    assert 'full_isolation_certified": False' in script
    assert 'check_container_observations(data)' in script
    assert 'SHA256SUMS' in script
