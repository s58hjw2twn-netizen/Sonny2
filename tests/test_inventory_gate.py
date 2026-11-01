from sonny.inventory_gate import InventoryItem, RenderedItem, reconcile_inventory, audit_rendered_inventory


def inventory():
    return (InventoryItem('arch', 'Inflatable arch', 1, ('user-photo-arch',), ('dimensions-arch',), True),
            InventoryItem('lights', 'Ground light system', 1, ('user-statement',), ('product-spec',), True))


def rendered():
    return (RenderedItem('arch', 1), RenderedItem('lights', 1))


def test_valid_manifest_requires_manual_source_check():
    assert reconcile_inventory(inventory(), source_review_completed=True)['status'] == 'READY_FOR_MANUAL_SOURCE_CHECK'


def test_missing_specs_blocks():
    items = (InventoryItem('arch', 'Arch', 1, ('photo',), (), True),)
    assert 'MISSING_PRODUCT_SPECIFICATIONS' in reconcile_inventory(items, source_review_completed=True)['errors']


def test_duplicate_ids_block():
    assert 'DUPLICATE_ITEM_ID' in reconcile_inventory(inventory() + inventory(), source_review_completed=True)['errors']


def test_quantity_mismatch_detects_flyer_error():
    assert 'QUANTITY_MISMATCH' in audit_rendered_inventory(inventory(), (RenderedItem('arch', 1), RenderedItem('lights', 2)), independent_visual_check_completed=True)['errors']


def test_invented_item_detected():
    assert 'INVENTED_RENDERED_ITEMS' in audit_rendered_inventory(inventory(), rendered() + (RenderedItem('train', 1),), independent_visual_check_completed=True)['errors']


def test_missing_item_detected():
    assert 'MISSING_RENDERED_ITEMS' in audit_rendered_inventory(inventory(), (RenderedItem('arch', 1),), independent_visual_check_completed=True)['errors']


def test_unchecked_or_false_verified_claim_fails():
    result = audit_rendered_inventory(inventory(), rendered(), independent_visual_check_completed=False, unsupported_verified_claim=True)
    assert 'VISUAL_CHECK_INCOMPLETE' in result['errors']
    assert 'UNSUPPORTED_VERIFIED_CLAIM' in result['errors']


def test_consistent_render_only_ready_for_human_approval():
    result = audit_rendered_inventory(inventory(), rendered(), independent_visual_check_completed=True)
    assert result['status'] == 'READY_FOR_HUMAN_APPROVAL'
    assert result['visual_authenticity_proven_by_code'] is False
