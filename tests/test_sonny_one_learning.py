from datetime import datetime, timedelta, timezone
import pytest
from sonny_one.life_memory import LifeMemory
from sonny_one.memory_policy import MemoryCandidate, MemoryStatus
from sonny_one.learning import Experience, propose_strategies

def test_memory_provenance_isolation_and_deletion(tmp_path):
    store = LifeMemory(str(tmp_path/"life.sqlite"))
    candidate = MemoryCandidate("alice","user-confirmed","Prefers concise reports",
                                MemoryStatus.VALIDATED,0.95,True)
    ident = store.add(candidate)
    assert len(store.recall("alice")) == 1
    assert store.recall("bob") == []
    assert store.recall("alice")[0].source == "user-confirmed"
    assert not store.revoke("bob", ident)
    assert store.revoke("alice", ident)
    assert store.recall("alice") == []

def test_unvalidated_memory_rejected(tmp_path):
    store = LifeMemory(str(tmp_path/"life.sqlite"))
    with pytest.raises(ValueError):
        store.add(MemoryCandidate("alice","model-inference","guess",consent=True))

def test_expired_memory_not_returned(tmp_path):
    store = LifeMemory(str(tmp_path/"life.sqlite"))
    candidate = MemoryCandidate("alice","user","old",MemoryStatus.VALIDATED,0.8,True)
    store.add(candidate,valid_until=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat())
    assert store.recall("alice",at=datetime.now(timezone.utc)+timedelta(days=1)) == []

def test_learning_only_from_verified_outcomes():
    items = [Experience("planning","checklist",True,True,"test") for _ in range(5)]
    items += [Experience("planning","guess",True,False,"") for _ in range(10)]
    proposals = propose_strategies(items)
    assert len(proposals) == 1
    assert proposals[0].status == "candidate-only"
    assert proposals[0].observed_success_rate == 1
