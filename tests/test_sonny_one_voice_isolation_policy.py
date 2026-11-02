from dataclasses import replace
import pytest
from sonny_one.voice_isolation_policy import IsolationEvidence, validate_isolation_evidence

@pytest.fixture
def evidence():
    return IsolationEvidence("linux-container", "docker", True, True, True,
                             1024**3, 32, 2.0, True, "independent-fixture")

def test_complete_evidence_passes_structural_validation(evidence):
    assert validate_isolation_evidence(evidence)

@pytest.mark.parametrize("field,value", [
    ("network_disabled", False), ("read_only_root", False),
    ("restricted_mounts", False), ("process_tree_kill_verified", False),
    ("independent_trial_id", ""), ("memory_limit_bytes", 0),
    ("process_limit", 0), ("cpu_limit", 0),
    ("platform", "unknown"),
])
def test_missing_isolation_control_fails(evidence, field, value):
    assert not validate_isolation_evidence(replace(evidence, **{field: value}))

def test_no_evidence_fails():
    with pytest.raises(TypeError):
        validate_isolation_evidence(None)
