import pytest
from sonny.paired_execution_review import summarize_pair

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def record(snapshot, code=0, command=C):
    return dict(snapshot_sha256=snapshot, command_sha256=command,
                exit_code=code, stdout_sha256=A, stderr_sha256=D)


def test_successful_candidate_remains_untrusted():
    result = summarize_pair(record(A), record(B))
    assert result["candidate_passed"] is True
    assert result["commit_allowed"] is False
    assert result["independently_verified"] is False
    assert result["evidence_authenticated"] is False


def test_regression_detected():
    result = summarize_pair(record(A), record(B, 1))
    assert result["regression"] is True
    assert result["candidate_passed"] is False


def test_different_commands_rejected():
    with pytest.raises(ValueError):
        summarize_pair(record(A), record(B, command=D))


def test_same_snapshot_rejected():
    with pytest.raises(ValueError):
        summarize_pair(record(A), record(A))


@pytest.mark.parametrize("bad", [
    {"exit_code": True},
    {"exit_code": -1},
    {"stdout_sha256": "invalid"},
    {"extra": "field"},
])
def test_invalid_evidence_rejected(bad):
    candidate = record(B)
    candidate.update(bad)
    with pytest.raises(ValueError):
        summarize_pair(record(A), candidate)
