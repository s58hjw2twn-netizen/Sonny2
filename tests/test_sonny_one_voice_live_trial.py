from pathlib import Path
import pytest
from sonny_one.voice_live_trial import run_trial

def args(tmp_path):
    pcm=tmp_path/"sample.pcm"
    pcm.write_bytes(b"\x00\x00")
    return dict(adapter_module="sonny_approved_fixture",provider_id="fixture",
                pcm_path=pcm,synthesis_text="hello")

@pytest.mark.parametrize("field",[
    "license_reviewed","installation_verified","network_disabled","owner_approved"
])
def test_missing_approval_fails_before_import(tmp_path,field):
    values=args(tmp_path)
    values.update({k:True for k in [
        "license_reviewed","installation_verified","network_disabled","owner_approved"
    ]})
    values[field]=False
    with pytest.raises(PermissionError):
        run_trial(**values)

def test_namespace_restriction(tmp_path):
    values=args(tmp_path)
    values["adapter_module"]="os"
    values.update(dict.fromkeys([
        "license_reviewed","installation_verified","network_disabled","owner_approved"
    ],True))
    with pytest.raises(PermissionError):
        run_trial(**values)

def test_missing_file_no_adapter_import(tmp_path):
    values=args(tmp_path)
    values["pcm_path"]=tmp_path/"missing.pcm"
    values["approved_adapter_modules"]=("sonny_approved_fixture",)
    values.update(dict.fromkeys([
        "license_reviewed","installation_verified","network_disabled","owner_approved"
    ],True))
    with pytest.raises(FileNotFoundError):
        run_trial(**values)

def test_unlisted_module_fails_before_import(tmp_path):
    values=args(tmp_path)
    values.update(dict.fromkeys([
        "license_reviewed","installation_verified","network_disabled","owner_approved"
    ],True))
    with pytest.raises(PermissionError):
        run_trial(**values)


def test_allowlisted_fixture_executes_and_returns_audit_record(tmp_path, monkeypatch):
    import sys
    from types import ModuleType
    from hashlib import sha256

    module = ModuleType("sonny_approved_fixture")
    class STT:
        def transcribe(self, pcm):
            return "fixture transcript"
    class TTS:
        def synthesize(self, text):
            return bytes(2)
    module.create_stt = STT
    module.create_tts = TTS
    monkeypatch.setitem(sys.modules, "sonny_approved_fixture", module)
    values = args(tmp_path)
    values["approved_adapter_modules"] = ("sonny_approved_fixture",)
    values.update(dict.fromkeys([
        "license_reviewed", "installation_verified",
        "network_disabled", "owner_approved"
    ], True))
    result = run_trial(**values)
    assert result["provider_id"] == "fixture"
    assert result["transcript"] == "fixture transcript"
    assert result["input_sha256"] == sha256(bytes(2)).hexdigest()
    assert result["output_sha256"] == sha256(bytes(2)).hexdigest()
    assert result["output_bytes"] == 2
    assert result["elapsed_ms"] >= 0
