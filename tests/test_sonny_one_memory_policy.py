from sonny_one.memory_policy import MemoryCandidate, MemoryStatus, admission_decision, retrieval_allowed

def test_proposed_memory_not_promoted():
    m = MemoryCandidate("a", "conversation", "example", consent=True, confidence=0.9)
    assert admission_decision(m) == "hold-validation"

def test_quarantined_memory_blocked():
    m = MemoryCandidate("a", "conversation", "example", MemoryStatus.QUARANTINED, 0.99, True)
    assert not retrieval_allowed(m, "a")

def test_user_isolation_and_consent():
    m = MemoryCandidate("a", "conversation", "example", MemoryStatus.VALIDATED, 0.9, True)
    assert retrieval_allowed(m, "a")
    assert not retrieval_allowed(m, "b")
    assert admission_decision(MemoryCandidate("a", "conversation", "example", MemoryStatus.VALIDATED, 0.9, False)) == "reject-no-consent"
