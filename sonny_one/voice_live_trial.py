"""Opt-in real-model speech trial runner.

Imports only a user-specified installed Python adapter module. Does not install
dependencies, fetch weights, open sockets, or infer that an adapter is safe.
Use an externally enforced network-restricted sandbox for untrusted adapters.
"""
import argparse
import importlib
import json
from dataclasses import asdict
from pathlib import Path

from sonny_one.voice_engine_probe import run_speech_probe
from sonny_one.voice_provider_boundary import LocalSpeechApproval, LocalSpeechBoundary

def run_trial(*, adapter_module, provider_id, pcm_path, synthesis_text,\n              approved_adapter_modules=(),
              license_reviewed=False, installation_verified=False,
              network_disabled=False, owner_approved=False):
    approval = LocalSpeechApproval(
        provider_id=provider_id, license_reviewed=license_reviewed,
        installation_verified=installation_verified,
        network_disabled=network_disabled, owner_approved=owner_approved,
    )
    approval.verify()  # Must fail before importing potentially privileged adapter code.
    if not isinstance(adapter_module, str) or not adapter_module.startswith("sonny_approved_"):
        raise ValueError("approved adapter module namespace required")
    if not isinstance(pcm_path, Path):
        raise TypeError("Path required")
    pcm = pcm_path.read_bytes()
    module = importlib.import_module(adapter_module)
    stt = module.create_stt()
    tts = module.create_tts()
    boundary = LocalSpeechBoundary(approval=approval, stt=stt, tts=tts)
    try:
        result = run_speech_probe(
            boundary, provider_id=provider_id, pcm=pcm,
            synthesis_text=synthesis_text,
        )
        return asdict(result)
    finally:
        boundary.close()

def main():
    parser = argparse.ArgumentParser(description="Explicit approved live speech probe")
    parser.add_argument("--adapter-module", required=True)\n    parser.add_argument("--allow-adapter-module", action="append", default=[],\n                        help="Explicitly trusted adapter module; approval is external")
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--pcm-file", type=Path, required=True)
    parser.add_argument("--synthesis-text", required=True)
    for flag in ("license-reviewed", "installation-verified", "network-disabled", "owner-approved"):
        parser.add_argument("--" + flag, action="store_true")
    args = parser.parse_args()
    result = run_trial(
        adapter_module=args.adapter_module, provider_id=args.provider_id,\n        approved_adapter_modules=tuple(args.allow_adapter_module),
        pcm_path=args.pcm_file, synthesis_text=args.synthesis_text,
        license_reviewed=args.license_reviewed,
        installation_verified=args.installation_verified,
        network_disabled=args.network_disabled, owner_approved=args.owner_approved,
    )
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
