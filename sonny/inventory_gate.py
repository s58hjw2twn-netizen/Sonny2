"""Fail-closed inventory reconciliation and output audit.

Provenance identifiers refer to evidence independently inspected by a caller.
This module validates consistency, not authenticity of source files.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryItem:
    item_id: str
    name: str
    quantity: int
    evidence_ids: tuple[str, ...]
    product_spec_ids: tuple[str, ...]
    verified: bool


@dataclass(frozen=True)
class RenderedItem:
    item_id: str
    quantity: int


def reconcile_inventory(items: tuple[InventoryItem, ...], *,
                        source_review_completed: bool) -> dict:
    errors = []
    if not items:
        errors.append('EMPTY_INVENTORY')
    ids = [i.item_id for i in items]
    if len(ids) != len(set(ids)):
        errors.append('DUPLICATE_ITEM_ID')
    for item in items:
        if not item.item_id.strip() or not item.name.strip():
            errors.append('MISSING_ITEM_ID_OR_NAME')
        if type(item.quantity) is not int or item.quantity <= 0:
            errors.append('INVALID_QUANTITY')
        if not item.evidence_ids or not all(x.strip() for x in item.evidence_ids):
            errors.append('MISSING_SOURCE_EVIDENCE')
        if not item.product_spec_ids or not all(x.strip() for x in item.product_spec_ids):
            errors.append('MISSING_PRODUCT_SPECIFICATIONS')
        if not item.verified:
            errors.append('UNVERIFIED_ITEM')
    if not source_review_completed:
        errors.append('SOURCE_REVIEW_INCOMPLETE')
    errors = sorted(set(errors))
    return {'status': 'BLOCKED' if errors else 'READY_FOR_MANUAL_SOURCE_CHECK',
            'errors': errors, 'authenticity_independently_established': False}


def audit_rendered_inventory(items: tuple[InventoryItem, ...],
                             rendered: tuple[RenderedItem, ...], *,
                             independent_visual_check_completed: bool,
                             unsupported_verified_claim: bool = False) -> dict:
    errors = []
    baseline = reconcile_inventory(items, source_review_completed=True)
    if baseline['errors']:
        errors.append('INVENTORY_NOT_RECONCILED')
    actual = {}
    for r in rendered:
        if not r.item_id.strip() or type(r.quantity) is not int or r.quantity <= 0:
            errors.append('INVALID_RENDERED_ITEM')
        if r.item_id in actual:
            errors.append('DUPLICATE_RENDERED_ITEM')
        actual[r.item_id] = r.quantity
    expected = {i.item_id: i.quantity for i in items}
    if set(expected) - set(actual):
        errors.append('MISSING_RENDERED_ITEMS')
    if set(actual) - set(expected):
        errors.append('INVENTED_RENDERED_ITEMS')
    if any(actual.get(k) != v for k, v in expected.items()):
        errors.append('QUANTITY_MISMATCH')
    if not independent_visual_check_completed:
        errors.append('VISUAL_CHECK_INCOMPLETE')
    if unsupported_verified_claim:
        errors.append('UNSUPPORTED_VERIFIED_CLAIM')
    errors = sorted(set(errors))
    return {'status': 'FAILED' if errors else 'READY_FOR_HUMAN_APPROVAL',
            'errors': errors, 'visual_authenticity_proven_by_code': False}
