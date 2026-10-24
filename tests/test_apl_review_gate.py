import pytest
from sonny_one.apl.metrics import compare_metrics
from sonny_one.apl.review_gate import assess_candidate

def fixture():
    b = {f"t{i}": 0.0 for i in range(20)}
    c = {f"t{i}": 1.0 for i in range(20)}
    e = {"status": "ELIGIBLE_FOR_HUMAN_REVIEW", "candidate_id": "abc",
         "base_revision": "rev", "lineage_hash": "hash"}
    a = {"local_lineage_verified": True, "runner_status": e["status"],
         "candidate_id": "abc", "base_revision": "rev", "lineage_hash": "hash",
         "promotion": "FORBIDDEN", "improvement_proven": False,
         "grader": "independent", "metrics": compare_metrics(b, c)}
    return e, a, b, c

def test_positive_only_recommends_review():
    e, a, b, c = fixture()
    r = assess_candidate(e, a, b, c, resamples=200)
    assert r["review_recommended"] is True
    assert r["promotion"] == "FORBIDDEN"
    assert r["recursive_improvement_proven"] is False

@pytest.mark.parametrize("field,value", [
    ("local_lineage_verified", False), ("grader", "candidate"),
    ("candidate_id", "different"), ("promotion", "ALLOWED"),
    ("runner_status", "REJECTED"),
])
def test_fail_closed_attachment(field, value):
    e, a, b, c = fixture()
    a[field] = value
    with pytest.raises(ValueError):
        assess_candidate(e, a, b, c, resamples=200)

def test_rejects_score_substitution():
    e, a, b, c = fixture()
    c["t0"] = 0.0
    with pytest.raises(ValueError):
        assess_candidate(e, a, b, c, resamples=200)

def test_no_gain_no_review():
    e, a, b, c = fixture()
    a["metrics"] = compare_metrics(b, b)
    assert assess_candidate(e, a, b, b, resamples=200)["review_recommended"] is False

def test_rejected_runner_fails_closed():
    e, a, b, c = fixture()
    e["status"] = "REJECTED"
    with pytest.raises(ValueError):
        assess_candidate(e, a, b, c, resamples=200)
