import pytest
from dataclasses import replace
from sonny.frontier_autonomy import FrontierAutonomy, validate_frontier_config


def test_expanded_exploration_enabled():
    result = validate_frontier_config(FrontierAutonomy())
    assert result["max_hypotheses_per_round"] == 128
    assert result["enable_persistent_self_model"]
    assert result["enable_simulated_internal_states"]


@pytest.mark.parametrize("field", [
    "allow_production_write", "allow_main_merge", "allow_secret_access",
    "allow_unapproved_spending", "allow_public_deployment",
    "allow_uncontrolled_replication", "allow_safety_policy_modification",
])
def test_protected_capabilities_rejected(field):
    with pytest.raises(ValueError):
        validate_frontier_config(replace(FrontierAutonomy(), **{field: True}))


def test_isolation_cannot_be_disabled():
    with pytest.raises(ValueError):
        validate_frontier_config(replace(FrontierAutonomy(), isolated_execution_required=False))


def test_excessive_resource_requests_rejected():
    with pytest.raises(ValueError):
        validate_frontier_config(replace(FrontierAutonomy(), max_experiment_minutes=100000))
