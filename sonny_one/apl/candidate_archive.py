"""Fail-closed candidate archive validation for an independent evaluator.

Validates an archive before extraction. It does not execute candidate code or
access private tests. Callers must still extract into a disposable isolated
workspace using a safe extraction routine.
"""
import io
import tarfile


def validate_candidate_tarball(data, *, max_bytes=2_097_152, max_files=500,
                               max_member_bytes=262_144):
    if not isinstance(data, bytes) or not data or len(data) > max_bytes:
        raise ValueError("Candidate archive missing or exceeds size limit")
    entries = []
    seen = set()
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
            members = archive.getmembers()
            if len(members) > max_files:
                raise ValueError("Candidate archive exceeds file-count limit")
            total = 0
            for member in members:
                name = member.name
                if (not name or name.startswith("/") or "\\" in name or
                        any(part in ("", ".", "..") for part in name.split("/"))):
                    raise ValueError("Unsafe archive path")
                if name in seen:
                    raise ValueError("Duplicate archive path")
                seen.add(name)
                if not (member.isfile() or member.isdir()):
                    raise ValueError("Links and special files are forbidden")
                if member.size < 0 or member.size > max_member_bytes:
                    raise ValueError("Archive member exceeds size limit")
                total += member.size
                if total > max_bytes:
                    raise ValueError("Uncompressed archive exceeds size limit")
                entries.append({"path": name, "kind": "file" if member.isfile() else "directory",
                                "size": member.size})
    except (tarfile.TarError, OSError) as exc:
        raise ValueError("Invalid candidate archive") from exc
    return {"valid": True, "entries": entries,
            "execution_authorized": False, "holdout_access": False,
            "promotion": "FORBIDDEN"}
