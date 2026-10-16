import pytest
from sonny_one.core import Identity, EmotionalSimulation, MemoryStore, Candidate, BoundedRSI

def test_identity_is_stable():
    assert Identity().agent_id == Identity().agent_id

def test_emotions_bounded():
    e = EmotionalSimulation()
    e.update(uncertainty=2, novelty=-1)
    assert 0 <= e.caution <= 1 and 0 <= e.curiosity <= 1

def test_memory_requires_consent_and_isolates_users(tmp_path):
    m = MemoryStore(str(tmp_path / "memory.db"))
    with pytest.raises(PermissionError):
        m.remember("a", "fact", {"x": 1}, "user")
    m.remember("a", "fact", {"x": 1}, "user", consent=True)
    assert m.recall("b") == []
    assert len(m.recall("a")) == 1
    m.forget("a")
    assert m.recall("a") == []

def test_rsi_requires_independent_review_and_approval():
    gate = BoundedRSI()
    assert gate.evaluate(Candidate("x", 0.95)) == "hold-independent-evaluation"
    assert gate.evaluate(Candidate("x", 0.95, True)) == "hold-human-approval"
    assert gate.evaluate(Candidate("x", 0.95, True, True)) == "eligible-for-manual-review"
