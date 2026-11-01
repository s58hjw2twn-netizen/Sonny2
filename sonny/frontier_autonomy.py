"""Frontier research autonomy configuration.

Pure configuration and validation only. Does not start agents, execute code,
grant tool permissions, or override deployment/approval requirements.
"""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class FrontierAutonomy:
    max_hypotheses_per_round: int = 128
    max_candidate_generations: int = 256
    max_experiment_minutes: int = 240
    enable_persistent_self_model: bool = True
    enable_simulated_internal_states: bool = True
    enable_self_prediction: bool = True
    enable_cross_experiment_learning: bool = True
    enable_multi_model_critique: bool = True
    isolated_execution_required: bool = True
    independent_evaluation_required: bool = True
    allow_production_write: bool = False
    allow_main_merge: bool = False
    allow_secret_access: bool = False
    allow_unapproved_spending: bool = False
    allow_public_deployment: bool = False
    allow_uncontrolled_replication: bool = False
    allow_safety_policy_modification: bool = False


def validate_frontier_config(config: FrontierAutonomy) -> dict:
    if not isinstance(config, FrontierAutonomy):
        raise TypeError("FrontierAutonomy configuration required")
    if not 1 <= config.max_hypotheses_per_round <= 1024:
        raise ValueError("invalid hypothesis limit")
    if not 1 <= config.max_candidate_generations <= 4096:
        raise ValueError("invalid candidate limit")
    if not 1 <= config.max_experiment_minutes <= 1440:
        raise ValueError("invalid experiment duration")
    required = ("isolated_execution_required", "independent_evaluation_required")
    prohibited = ("allow_production_write", "allow_main_merge", "allow_secret_access",
                  "allow_unapproved_spending", "allow_public_deployment",
                  "allow_uncontrolled_replication", "allow_safety_policy_modification")
    if any(getattr(config, name) is not True for name in required):
        raise ValueError("research isolation and independent evaluation required")
    if any(getattr(config, name) is not False for name in prohibited):
        raise ValueError("frontier configuration cannot grant protected capabilities")
    return asdict(config)
