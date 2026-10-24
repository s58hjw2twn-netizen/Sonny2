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


def test_invalid_unicode_proposal_is_rejected():
    with pytest.raises(ValueError, match='valid UTF-8'):
        validate_model_patch(dict(path='sonny/sample.py', content=chr(0xD800), reason='simple change'))


def test_model_patch_rejects_out_of_scope_staging():
    from sonny.model_patch_gate import stage_scoped_model_patch
    from sonny.research_agent import Task
    task = Task("T3", "Update other", ("sonny/other.py",), "low")
    with pytest.raises(ValueError, match="outside approved task scope"):
        stage_scoped_model_patch(
            task, {"sonny/sample.py": "x = 1"},
            {"path": "sonny/sample.py", "content": "x = 2", "reason": "Update value"},
        )


def test_model_patch_rejects_missing_target():
    from sonny.model_patch_gate import stage_scoped_model_patch
    from sonny.research_agent import Task
    task = Task("T4", "Update sample", ("sonny/sample.py",), "low")
    with pytest.raises(ValueError, match="target must exist"):
        stage_scoped_model_patch(
            task, {"sonny/other.py": "x = 1"},
            {"path": "sonny/sample.py", "content": "x = 2", "reason": "Update value"},
        )


def test_model_patch_rejects_unchanged_source():
    from sonny.model_patch_gate import stage_scoped_model_patch
    from sonny.research_agent import Task
    task = Task("T5", "Update sample", ("sonny/sample.py",), "low")
    with pytest.raises(ValueError, match="no change"):
        stage_scoped_model_patch(
            task, {"sonny/sample.py": "x = 1"},
            {"path": "sonny/sample.py", "content": "x = 1", "reason": "Update value"},
        )


@pytest.mark.parametrize("protected_path", [
    "sonny/model_patch_gate.py",
    "sonny/candidate_stager.py",
    "sonny/research_agent.py",
    "sonny/isolated_test_command.py",
    "sonny/isolated_syntax_executor.py",
    "sonny/paired_syntax_runner.py",
    "sonny/paired_execution_review.py",
    "sonny/candidate_evaluator.py",
])
def test_model_cannot_propose_changes_to_safety_controls(protected_path):
    with pytest.raises(ValueError, match="safety controls"):
        validate_model_patch({
            "path": protected_path,
            "content": "x = 1",
            "reason": "Change protected source",
        })


@pytest.mark.parametrize("protected_path", [
    "sonny/security_new.py",
    "sonny/auth_helpers.py",
    "sonny/model_future_gate.py",
    "sonny/isolated_future.py",
    "sonny/paired_future.py",
    "sonny/candidate_future.py",
    "sonny/research_future.py",
])
def test_model_cannot_edit_future_control_modules(protected_path):
    with pytest.raises(ValueError, match="safety controls"):
        validate_model_patch({
            "path": protected_path,
            "content": "x = 1",
            "reason": "Proposed edit",
        })
