"""Read-only Linux container isolation probe; emits JSON evidence, not approval."""
import json
from pathlib import Path

def probe():
    network = Path("/proc/net/route")
    routes = network.read_text().splitlines()[1:] if network.exists() else None
    default_route = (any(len(fields := line.split()) >= 2 and fields[1] == "00000000" for line in routes)\n                     if routes is not None else None)
    memory = Path("/sys/fs/cgroup/memory.max")
    pids = Path("/sys/fs/cgroup/pids.max")
    cpu = Path("/sys/fs/cgroup/cpu.max")
    return {
        "network_default_route_absent": (not default_route) if default_route is not None else None,
        "memory_max": memory.read_text().strip() if memory.exists() else None,
        "pids_max": pids.read_text().strip() if pids.exists() else None,
        "cpu_max": cpu.read_text().strip() if cpu.exists() else None,
        "root_mount": next((line for line in Path("/proc/mounts").read_text().splitlines()
                            if len(line.split()) >= 4 and line.split()[1] == "/"), None),
        "isolation_verified": False,
        "notes": "Read-only observations; no route does not prove all networking disabled.",
    }

if __name__ == "__main__":
    print(json.dumps(probe(), sort_keys=True))
