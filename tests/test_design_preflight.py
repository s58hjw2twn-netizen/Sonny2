from sonny.design_preflight import DesignEvidence, assess_design_readiness


def sample(**overrides):
    fields = dict(actual_property_photo_ids=("photo-1",),
                  inventory_item_ids=("tree-1", "wreath-1"),
                  verified_item_ids=("tree-1", "wreath-1"),
                  retailer_spec_item_ids=("tree-1", "wreath-1"),
                  source_review_completed=True, output_check_planned=True)
    fields.update(overrides)
    return DesignEvidence(**fields)


def test_full_manifest_is_only_ready_not_authenticated():
    result = assess_design_readiness(sample())
    assert result["status"] == "READY_FOR_DESIGN_WITH_VERIFICATION"
    assert result["may_claim_actual_or_to_scale"] is False


def test_missing_actual_house_blocks():
    assert "MISSING_ACTUAL_PROPERTY_PHOTOS" in assess_design_readiness(
        sample(actual_property_photo_ids=()))["failures"]


def test_missing_retailer_size_blocks():
    assert "MISSING_RETAILER_SPECIFICATIONS" in assess_design_readiness(
        sample(retailer_spec_item_ids=("tree-1",)))["failures"]


def test_invented_inventory_cannot_pass():
    result = assess_design_readiness(sample(inventory_item_ids=("tree-1", "wreath-1", "fake-1")))
    assert "UNVERIFIED_INVENTORY_ITEMS" in result["failures"]
    assert "MISSING_RETAILER_SPECIFICATIONS" in result["failures"]


def test_skipped_independent_check_blocks():
    assert assess_design_readiness(sample(output_check_planned=False))["status"] == "BLOCKED_MISSING_EVIDENCE"
