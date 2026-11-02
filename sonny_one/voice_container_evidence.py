"""Evaluate observed cgroup and mount limits; not an isolation certificate."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ContainerObservations:
    network_default_route_absent: bool
    memory_max: str
    pids_max: str
    cpu_max: str
    root_mount: str

def check_container_observations(data: dict) -> tuple[bool, tuple[str, ...]]:
    failures = []
    if not isinstance(data, dict):
        return False, ("probe result must be a mapping",)
    if data.get("isolation_verified") is not False:
        failures.append("probe must not self-certify")
    if data.get("network_default_route_absent") is not True:
        failures.append("default route observed or unavailable")
    if data.get("memory_max") != str(512 * 1024 * 1024):
        failures.append("memory cgroup limit mismatch")
    if data.get("pids_max") != "32":
        failures.append("process cgroup limit mismatch")
    cpu = data.get("cpu_max")
    if not isinstance(cpu, str) or len(cpu.split()) != 2:
        failures.append("CPU cgroup missing")
    else:
        try:
            quota, period = (int(part) for part in cpu.split())
            if quota <= 0 or period <= 0 or quota > period:
                failures.append("CPU quota not capped at one core")
        except ValueError:
            failures.append("CPU cgroup invalid")
    root = data.get("root_mount")
    fields = root.split() if isinstance(root, str) else []
    if len(fields) < 4 or fields[1] != "/" or "ro" not in fields[3].split(","):
        failures.append("root filesystem not observed read-only")
    return not failures, tuple(failures)
