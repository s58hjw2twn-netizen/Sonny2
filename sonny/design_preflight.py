"""Pre-generation gate for user-specific visual designs.

Checks evidence completeness, not the authenticity of supplied evidence.
Callers must independently retrieve/verify source material and compare output.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DesignEvidence:
    actual_property_photo_ids: tuple[str, ...]
    inventory_item_ids: tuple[str, ...]
    verified_item_ids: tuple[str, ...]
    retailer_spec_item_ids: tuple[str, ...]
    source_review_completed: bool
    output_check_planned: bool


def assess_design_readiness(evidence: DesignEvidence) -> dict:
    if not isinstance(evidence, DesignEvidence):
        raise TypeError("DesignEvidence required")
    inventory = set(evidence.inventory_item_ids)
    verified = set(evidence.verified_item_ids)
    specified = set(evidence.retailer_spec_item_ids)
    failures = []
    if not evidence.actual_property_photo_ids or not all(evidence.actual_property_photo_ids):
        failures.append("MISSING_ACTUAL_PROPERTY_PHOTOS")
    if not inventory or not all(inventory):
        failures.append("MISSING_INVENTORY")
    if inventory - verified:
        failures.append("UNVERIFIED_INVENTORY_ITEMS")
    if inventory - specified:
        failures.append("MISSING_RETAILER_SPECIFICATIONS")
    if not evidence.source_review_completed:
        failures.append("SOURCE_REVIEW_NOT_COMPLETED")
    if not evidence.output_check_planned:
        failures.append("INDEPENDENT_OUTPUT_CHECK_NOT_PLANNED")
    return {
        "status": "BLOCKED_MISSING_EVIDENCE" if failures else "READY_FOR_DESIGN_WITH_VERIFICATION",
        "failures": failures,
        "may_claim_actual_or_to_scale": False,
        "authenticity_independently_established": False,
    }
