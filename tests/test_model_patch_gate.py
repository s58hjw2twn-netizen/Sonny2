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
