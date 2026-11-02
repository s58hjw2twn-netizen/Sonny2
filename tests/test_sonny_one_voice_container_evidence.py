from copy import deepcopy
import pytest
from sonny_one.voice_container_evidence import check_container_observations

@pytest.fixture
def observations():
    return {
        "isolation_verified": False,
        "network_default_route_absent": True,
        "memory_max": str(512 * 1024 * 1024),
        "pids_max": "32",
        "cpu_max": "100000 100000",
        "root_mount": "overlay / overlay ro,relatime 0 0",
    }

def test_expected_observations_are_structurally_accepted(observations):
    assert check_container_observations(observations) == (True, ())

@pytest.mark.parametrize("field,value", [
    ("isolation_verified", True), ("network_default_route_absent", False),
    ("memory_max", "max"), ("pids_max", "max"),
    ("cpu_max", "max 100000"), ("cpu_max", "200000 100000"),
    ("root_mount", "overlay / overlay rw,relatime 0 0"),
])
def test_missing_or_weakened_control_rejected(observations, field, value):
    observations[field] = value
    ok, failures = check_container_observations(observations)
    assert not ok and failures

def test_missing_fields_rejected():
    ok, failures = check_container_observations({})
    assert not ok and failures

def test_non_mapping_rejected():
    assert not check_container_observations(None)[0]
