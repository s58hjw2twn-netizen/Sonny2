"""Validate a privacy-conscious real-photo evaluation manifest.

This validates provenance and review metadata, not image identity.
"""
from pathlib import Path

def validate_manifest(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("pairs"), list):
        raise ValueError("pairs list required")
    pairs = manifest["pairs"]
    if not pairs:
        raise ValueError("at least one pair required")
    ids = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError("invalid pair")
        identifier = pair.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError("missing or duplicate pair id")
        ids.add(identifier)
        if pair.get("consent_confirmed") is not True:
            raise ValueError("explicit consent required")
        if pair.get("owner_review_required") is not True:
            raise ValueError("owner review required")
        for field in ("original_sha256", "restored_sha256"):
            value = pair.get(field)
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("invalid sha256")
        if pair["original_sha256"] == pair["restored_sha256"]:
            raise ValueError("original and restored files must differ")
        if "image_path" in pair or "face_embedding" in pair:
            raise ValueError("private image paths and biometric embeddings prohibited in manifest")
    return {"pairs_validated":len(pairs),"consent_metadata_present":True,
            "image_bytes_verified":False,"identity_verified":False,
            "release_allowed":False}
