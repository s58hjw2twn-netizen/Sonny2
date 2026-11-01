"""Fail-closed source/constraint/output gate for user-authorized changes.

This gate validates submitted evidence and audit results; it does NOT inspect images,
retrieve sources, authenticate evidence, or certify physical scale on its own.
"""
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ChangeContract:
    source_ids: tuple[str, ...]
    source_reviewed: bool
    authorized_changes: tuple[str, ...]
    protected_elements: tuple[str, ...]
    required_inventory: Mapping[str, int]
    measured_dimensions: Mapping[str, float]
    independent_output_check: bool
    output_source_match: bool
    protected_elements_preserved: bool
    dimensions_checked: bool
    rendered_inventory: Mapping[str, int]
    unauthorized_additions: tuple[str, ...] = ()


def assess_change(contract: ChangeContract) -> dict:
    """Require explicit independent checks; never infer successful verification."""
    if not isinstance(contract, ChangeContract):
        raise TypeError("ChangeContract required")
    failures = []
    if not contract.source_ids or any(not isinstance(x, str) or not x.strip() for x in contract.source_ids):
        failures.append("SOURCE_MISSING")
    if not contract.source_reviewed:
        failures.append("SOURCE_NOT_REVIEWED")
    if not contract.authorized_changes or any(not isinstance(x, str) or not x.strip() for x in contract.authorized_changes):
        failures.append("CHANGE_SCOPE_MISSING")
    if set(contract.authorized_changes) & set(contract.protected_elements):
        failures.append("PROTECTED_SCOPE_CONFLICT")
    if not contract.independent_output_check:
        failures.append("OUTPUT_NOT_INDEPENDENTLY_CHECKED")
    if not contract.output_source_match:
        failures.append("SOURCE_MISMATCH")
    if not contract.protected_elements_preserved:
        failures.append("PROTECTED_ELEMENT_CHANGED")
    if not contract.dimensions_checked:
        failures.append("DIMENSIONS_NOT_CHECKED")
    if not contract.measured_dimensions or any(
        not isinstance(v, (int, float)) or isinstance(v, bool) or not (0 < v < float('inf'))
        for v in contract.measured_dimensions.values()
    ):
        failures.append("DIMENSIONS_MISSING_OR_INVALID")
    expected = dict(contract.required_inventory)
    actual = dict(contract.rendered_inventory)
    if not expected or any(not isinstance(k, str) or not k.strip() or type(v) is not int or v < 1 for k, v in expected.items()):
        failures.append("INVENTORY_INVALID")
    if any(not isinstance(k, str) or not k.strip() or type(v) is not int or v < 1 for k, v in actual.items()):
        failures.append("RENDERED_INVENTORY_INVALID")
    if expected != actual:
        failures.append("INVENTORY_MISMATCH")
    if contract.unauthorized_additions:
        failures.append("UNAUTHORIZED_ADDITIONS")
    failures = sorted(set(failures))
    return {
        "status": "BLOCKED" if failures else "READY_FOR_HUMAN_REVIEW",
        "failures": failures,
        "independently_verified_by_this_module": False,
        "may_claim_photographic_or_scale_authenticity": False,
    }
