"""Declarative evidence gate. This is not an isolation implementation."""
from dataclasses import dataclass

@dataclass(frozen=True)
class IsolationEvidence:
    platform: str
    executor: str
    network_disabled: bool
    read_only_root: bool
    restricted_mounts: bool
    memory_limit_bytes: int
    process_limit: int
    cpu_limit: float
    process_tree_kill_verified: bool
    independent_trial_id: str

def validate_isolation_evidence(evidence: IsolationEvidence) -> bool:
    if not isinstance(evidence, IsolationEvidence):
        raise TypeError("IsolationEvidence required")
    if evidence.platform not in ("linux-container", "windows-sandbox"):
        return False
    if not evidence.executor or not evidence.independent_trial_id:
        return False
    if not (evidence.network_disabled and evidence.read_only_root and
            evidence.restricted_mounts and evidence.process_tree_kill_verified):
        return False
    if type(evidence.memory_limit_bytes) is not int or not 256 * 1024**2 <= evidence.memory_limit_bytes <= 8 * 1024**3:
        return False
    if type(evidence.process_limit) is not int or not 1 <= evidence.process_limit <= 64:
        return False
    if type(evidence.cpu_limit) not in (int, float) or not 0 < evidence.cpu_limit <= 8:
        return False
    return True
