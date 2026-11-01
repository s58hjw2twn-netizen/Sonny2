"""Fail-closed evidence gate for source-grounded design specifications.

No network retrieval is performed here. Callers must independently verify source
authenticity and supply evidence; unverified inputs never become verified claims.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse


@dataclass(frozen=True)
class Evidence:
    object_id: str
    attribute: str
    value: str
    source_url: str
    source_kind: str
    verified: bool = False


def validate_evidence(evidence: Evidence, required_source_host: str) -> bool:
    """Check declared provenance and explicit verification; not source authenticity."""
    if not all((evidence.object_id.strip(), evidence.attribute.strip(),
                evidence.value.strip(), required_source_host.strip())):
        return False
    if not evidence.verified or evidence.source_kind not in {"listing", "manufacturer", "user_image"}:
        return False
    parsed = urlparse(evidence.source_url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    expected = required_source_host.lower().rstrip(".")
    return host == expected or host.endswith("." + expected)


def require_verified(evidence: Evidence, required_source_host: str) -> str:
    if not validate_evidence(evidence, required_source_host):
        raise ValueError("Unverified or mismatched evidence; do not use in design")
    return evidence.value


def validate_positive_dimension(value: str) -> Decimal:
    try:
        dimension = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid dimension") from None
    if not dimension.is_finite() or dimension <= 0:
        raise ValueError("Dimension must be finite and positive")
    return dimension
