import pytest

from sonny_one.apl.custody import seal_evidence
from sonny_one.apl.custody_review import review_custodied_apl_evidence

KEY = b"local-test-only-independent-custodian-key-32bytes"
EVALUATION = {
    "candidate_id": "a" * 64,
    "base_revision": "b" * 40,
    "trusted_suite_sha256": "c" * 64,
    "heldout_suite_sha256": "d" * 64,
    "image": "test@sha256:" + "e" * 64,
    "status": "ELIGIBLE_FOR_REVIEW",
    "promotion": "FORBIDDEN",
}


def record():
    return {
        **{k: EVALUATION[k] for k in (
            "candidate_id", "base_revision", "trusted_suite_sha256",
            "heldout_suite_sha256", "image")},
        "runner_status": EVALUATION["status"],
        "promotion": "FORBIDDEN",
    }


def test_valid_custody_still_requires_replication():
    item = record()
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    result = review_custodied_apl_evidence(
        EVALUATION, item, envelope, KEY, "independent-test")
    assert result["custody_envelope_valid"] is True
    assert result["independently_verified"] is False
    assert result["commit_allowed"] is False
    assert result["promotion_allowed"] is False


def test_wrong_custodian_fails_closed():
    item = record()
    envelope = seal_evidence(item, KEY, custodian_id="wrong")
    result = review_custodied_apl_evidence(
        EVALUATION, item, envelope, KEY, "independent-test")
    assert result["custody_envelope_valid"] is False


def test_tampered_identity_rejected_even_if_resigned():
    item = record()
    item["candidate_id"] = "f" * 64
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    with pytest.raises(ValueError, match="does not match"):
        review_custodied_apl_evidence(
            EVALUATION, item, envelope, KEY, "independent-test")


def test_promotion_claim_rejected():
    item = record()
    item["promotion"] = "ALLOWED"
    envelope = seal_evidence(item, KEY, custodian_id="independent-test")
    with pytest.raises(ValueError, match="promotion boundary"):
        review_custodied_apl_evidence(
            EVALUATION, item, envelope, KEY, "independent-test")
