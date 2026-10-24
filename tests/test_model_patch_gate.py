import pytest
from sonny.model_patch_gate import validate_model_patch

def test_accepts_bounded_proposal_without_commit_authority():
    result = validate_model_patch(dict(path='sonny/sample.py', content='x = 1', reason='simple change'))
    assert result['content_bytes'] == 5
    assert result['commit_allowed'] is False
    assert result['approved_for_staging'] is False

def test_rejects_unapproved_path():
    with pytest.raises(ValueError):
        validate_model_patch(dict(path='docs/sample.txt', content='x = 1', reason='simple change'))

def test_rejects_oversized_proposal():
    with pytest.raises(ValueError):
        validate_model_patch(dict(path='sonny/sample.py', content='x' * 32001, reason='simple change'))

def test_rejects_unexpected_field():
    with pytest.raises(ValueError):
        validate_model_patch(dict(path='sonny/sample.py', content='x = 1', reason='simple change', approved=True))


def test_scoped_patch_accepts_matching_task():
    from sonny.model_patch_gate import validate_scoped_model_patch
    result = validate_scoped_model_patch(dict(path='sonny/sample.py', content='x = 1', reason='simple change'), ('sonny/sample.py',))
    assert result['commit_allowed'] is False


def test_scoped_patch_rejects_unapproved_target():
    from sonny.model_patch_gate import validate_scoped_model_patch
    with pytest.raises(ValueError, match='outside approved task scope'):
        validate_scoped_model_patch(dict(path='sonny/sample.py', content='x = 1', reason='simple change'), ('sonny/other.py',))


def test_model_patch_stages_in_memory_without_commit():
    from sonny.model_patch_gate import stage_scoped_model_patch
    from sonny.research_agent import Task
    task = Task("T1", "Update sample", ("sonny/sample.py",), "low")
    result = stage_scoped_model_patch(
        task, {"sonny/sample.py": "x = 1"},
        {"path": "sonny/sample.py", "content": "x = 2", "reason": "Update value"},
    )
    assert result["candidate"]["sonny/sample.py"] == "x = 2"
    assert result["writes_performed"] == 0
    assert result["execution_allowed"] is False
    assert result["commit_allowed"] is False


def test_model_patch_rejects_medium_risk_task():
    from sonny.model_patch_gate import stage_scoped_model_patch
    from sonny.research_agent import Task
    task = Task("T2", "Update sample", ("sonny/sample.py",), "medium")
    with pytest.raises(ValueError, match="low-risk"):
        stage_scoped_model_patch(
            task, {"sonny/sample.py": "x = 1"},
            {"path": "sonny/sample.py", "content": "x = 2", "reason": "Update value"},
        )
