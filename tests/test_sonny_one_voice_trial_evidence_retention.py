from pathlib import Path

def test_trial_hashes_assessment_before_failure_exit():
    script = Path("scripts/sonny_voice_container_trial.sh").read_text()
    assessment = script.index('"assessment.json"')
    hashes = script.index('sha256sum probe.json assessment.json > SHA256SUMS')
    failed_exit = script.index('raise SystemExit("Container observations failed; retained hashed evidence")')
    assert assessment < hashes < failed_exit

def test_trial_never_executes_unapproved_image_pull():
    script = Path("scripts/sonny_voice_container_trial.sh").read_text()
    assert "--pull never" in script
    assert 'docker image inspect "$image"' in script
