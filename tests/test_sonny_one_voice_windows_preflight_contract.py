"""Static safety contract for the Windows read-only diagnostic.

Not a substitute for executing the script on Windows.
"""
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sonny_voice_windows_preflight.ps1"

def test_preflight_exists_and_reports_unverified_gates():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "ModelInstalledVerified = $false" in text
    assert "AudioDeviceTested = $false" in text
    assert "NetworkIsolationVerified = $false" in text

def test_preflight_does_not_contain_install_or_download_commands():
    text = SCRIPT.read_text(encoding="utf-8").lower()
    forbidden = (
        "invoke-webrequest", "invoke-restmethod", "start-bitstransfer",
        "install-package", "install-module", "winget install",
        "choco install", "set-executionpolicy", "set-itemproperty",
        "remove-item", "new-item", "start-process",
    )
    for command in forbidden:
        assert command not in text, command
