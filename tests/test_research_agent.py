import pytest

from sonny.research_agent import Task, plan


def test_plan_creates_reviewable_batch_without_execution():
    result = plan([
        Task("t1", "Improve memory tests", ("tests/test_memory.py",)),
        Task("t2", "Document agent", ("docs/agent.md",), "medium"),
    ])
    assert result["mode"] == "plan-only"
    assert result["writes_performed"] == 0
    assert result["model_calls"] == 0
    assert len(result["tasks"]) == 2
    assert all(not task["execution_allowed"] for task in result["tasks"])


@pytest.mark.parametrize("path", [
    "../secrets", "/etc/passwd", "sonny/../.github/workflows/ci.yml",
    ".github/workflows/ci.yml", "evaluation/frozen.json",
    "sonny\\secret.py", "sonny//module.py",
])
def test_forbidden_paths_rejected(path):
    with pytest.raises(ValueError):
        plan([Task("bad", "bad path", (path,))])


def test_duplicate_task_ids_rejected():
    with pytest.raises(ValueError):
        plan([
            Task("same", "first", ("sonny/one.py",)),
            Task("same", "second", ("tests/test_one.py",)),
        ])


def test_batch_limit_enforced():
    with pytest.raises(ValueError):
        plan([Task(str(i), "task", ("docs/plan.md",)) for i in range(9)])


def test_high_risk_is_never_automatically_approved():
    result = plan([Task("risky", "security review", ("sonny/auth.py",), "high")])
    assert result["tasks"][0]["execution_allowed"] is False
