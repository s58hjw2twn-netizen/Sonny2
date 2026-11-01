"""Independent regression checks for the source-evidence gate."""
import pytest
from sonny.source_verification import Evidence, require_verified, validate_positive_dimension


def sample(**changes):
    values = dict(object_id="arch-001", attribute="width_ft", value="12",
                  source_url="https://www.amazon.com/example", source_kind="listing",
                  verified=True)
    values.update(changes)
    return Evidence(**values)


def test_verified_exact_source():
    assert require_verified(sample(), "amazon.com") == "12"


@pytest.mark.parametrize("changes", [
    {"verified": False},
    {"source_url": "https://amazon.com.evil.example/item"},
    {"source_url": "http://www.amazon.com/item"},
    {"source_url": "https://evil.example/item"},
    {"source_url": "https://user:password@amazon.com/item"},
    {"source_kind": "guess"},
    {"value": ""},
])
def test_rejects_unverified_or_bad_source(changes):
    with pytest.raises(ValueError):
        require_verified(sample(**changes), "amazon.com")


def test_source_specificity():
    with pytest.raises(ValueError):
        require_verified(sample(), "homedepot.com")


@pytest.mark.parametrize("bad", ["0", "-1", "NaN", "Infinity", "twelve", ""])
def test_bad_dimensions(bad):
    with pytest.raises(ValueError):
        validate_positive_dimension(bad)


def test_valid_dimension():
    assert str(validate_positive_dimension("12.5")) == "12.5"
