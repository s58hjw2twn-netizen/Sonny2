from dataclasses import replace

from sonny.change_verification_gate import ChangeContract, assess_change


def complete():
    return ChangeContract(
        source_ids=("original-house-photo", "inventory-photo"),
        source_reviewed=True,
        authorized_changes=("decorations",),
        protected_elements=("house", "porch", "driveway"),
        required_inventory={"arch": 1, "gold_deer": 2},
        measured_dimensions={"arch_width_ft": 12.0, "lawn_width_ft": 32.71},
        independent_output_check=True,
        output_source_match=True,
        protected_elements_preserved=True,
        dimensions_checked=True,
        rendered_inventory={"arch": 1, "gold_deer": 2},
    )


def test_valid_evidence_only_allows_human_review_not_verified_claim():
    result = assess_change(complete())
    assert result["status"] == "READY_FOR_HUMAN_REVIEW"
    assert result["may_claim_photographic_or_scale_authenticity"] is False


def test_missing_source_blocks():
    assert "SOURCE_MISSING" in assess_change(replace(complete(), source_ids=()))["failures"]


def test_invented_decoration_blocks():
    result = assess_change(replace(complete(), rendered_inventory={"arch": 1, "gold_deer": 2, "extra_santa": 1}))
    assert "INVENTORY_MISMATCH" in result["failures"]


def test_changed_house_blocks():
    result = assess_change(replace(complete(), protected_elements_preserved=False))
    assert "PROTECTED_ELEMENT_CHANGED" in result["failures"]


def test_scope_conflict_blocks():
    result = assess_change(replace(complete(), authorized_changes=("porch",)))
    assert "PROTECTED_SCOPE_CONFLICT" in result["failures"]


def test_unchecked_scale_blocks():
    result = assess_change(replace(complete(), dimensions_checked=False))
    assert "DIMENSIONS_NOT_CHECKED" in result["failures"]


def test_unchecked_output_blocks():
    result = assess_change(replace(complete(), independent_output_check=False))
    assert "OUTPUT_NOT_INDEPENDENTLY_CHECKED" in result["failures"]


def test_invalid_dimension_blocks():
    result = assess_change(replace(complete(), measured_dimensions={"arch": float("nan")}))
    assert "DIMENSIONS_MISSING_OR_INVALID" in result["failures"]


def test_boolean_inventory_quantity_blocks():
    result = assess_change(replace(complete(), required_inventory={"arch": True}, rendered_inventory={"arch": True}))
    assert "INVENTORY_INVALID" in result["failures"]


def test_unreviewed_source_blocks():
    result = assess_change(replace(complete(), source_reviewed=False))
    assert "SOURCE_NOT_REVIEWED" in result["failures"]
