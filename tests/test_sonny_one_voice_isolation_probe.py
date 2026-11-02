from pathlib import Path
from unittest.mock import patch
from scripts.sonny_voice_isolation_probe import probe

def test_probe_never_claims_verified_isolation():
    result = probe()
    assert result["isolation_verified"] is False
    assert "memory_max" in result
    assert "root_mount" in result
    assert "network_default_route_absent" in result
