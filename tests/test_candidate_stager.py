import pytest

from sonny.research_agent import Task
from sonny.candidate_stager import Replacement, stage_candidate


def test_candidate_is_deterministic_and_does_not_mutate_original():
    files = {"sonny/example.py": "value = 1\n"}
    task = Task("t1", "Improve example", ("sonny/example.py",))
    changes = [Replacement("sonny/example.py", "value = 1", "value = 2")]
    first = stage_candidate(task, files, changes)
    second = stage_candidate(task, files, changes)
    assert first["candidate"]["sonny/example.py"] == "value = 2\n"
    assert files["sonny/example.py"] == "value = 1\n"
    assert first["sha256"] == second["sha256"]
    assert first["writes_performed"] == 0
    assert first["execution_allowed"] is False


def test_out_of_scope_patch_is_rejected():
    task = Task("t1", "Update tests", ("tests/test_a.py",))
    with pytest.raises(ValueError):
        stage_candidate(task, {"sonny/app.py": "x"}, [
            Replacement("sonny/app.py", "x", "y")
        ])


def test_ambiguous_anchor_is_rejected():
    task = Task("t1", "Update", ("sonny/a.py",))
    with pytest.raises(ValueError):
        stage_candidate(task, {"sonny/a.py": "x x"}, [
            Replacement("sonny/a.py", "x", "y")
        ])


def test_high_risk_changes_cannot_be_staged():
    task = Task("t1", "Security", ("sonny/app.py",), "high")
    with pytest.raises(ValueError):
        stage_candidate(task, {"sonny/app.py": "x"}, [
            Replacement("sonny/app.py", "x", "y")
        ])


def test_missing_file_cannot_be_created_implicitly():
    task = Task("t1", "Update", ("sonny/missing.py",))
    with pytest.raises(ValueError):
        stage_candidate(task, {}, [Replacement("sonny/missing.py", "x", "y")])
