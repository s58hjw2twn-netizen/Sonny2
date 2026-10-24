import pytest

from sonny.research_agent import Task
from sonny.candidate_stager import Replacement, stage_candidate
from sonny.candidate_evaluator import evaluate_candidate, fingerprint


def candidate():
    return stage_candidate(
        Task("t1", "Improve deterministic function", ("sonny/sample.py",)),
        {"sonny/sample.py": "answer = 1\n"},
        [Replacement("sonny/sample.py", "answer = 1", "answer = 2")],
    )


def test_fingerprint_matches_stager():
    staged = candidate()
    assert fingerprint(staged["candidate"]) == staged["sha256"]


def test_passed_checks_do_not_authorize_commit():
    result = evaluate_candidate(candidate(), {"unit": True}, {"unit": True})
    assert result["passed"] is True
    assert result["commit_allowed"] is False
    assert result["tests_executed_by_evaluator"] == 0


def test_regression_blocks_candidate():
    result = evaluate_candidate(
        candidate(), {"unit": True, "new": False},
        {"unit": False, "new": True},
    )
    assert result["passed"] is False
    assert result["regressions"] == ["unit"]


def test_tampered_candidate_is_rejected():
    staged = candidate()
    staged["candidate"]["sonny/sample.py"] = "answer = 999\n"
    with pytest.raises(ValueError, match="fingerprint"):
        evaluate_candidate(staged, {"unit": True}, {"unit": True})


def test_unpaired_checks_rejected():
    with pytest.raises(ValueError, match="paired"):
        evaluate_candidate(candidate(), {"unit": True}, {"other": True})
