from pathlib import Path
from unittest.mock import patch
from scripts.sonny_voice_isolation_probe import probe

def test_probe_never_claims_verified_isolation():
    result = probe()
    assert result["isolation_verified"] is False
    assert "memory_max" in result
    assert "root_mount" in result
    assert "network_default_route_absent" in result

def test_missing_route_evidence_fails_closed():
    original_exists = Path.exists
    def missing_route_only(path):
        if str(path) == "/proc/net/route":
            return False
        return original_exists(path)
    with patch.object(Path, "exists", missing_route_only):
        result = probe()
    assert result["network_default_route_absent"] is None
