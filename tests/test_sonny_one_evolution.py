from sonny_one.evolution import Evaluation, evaluate_challenger, FROZEN_REFERENCES

def test_references_preserved():
    assert "CSAT-1.3" in FROZEN_REFERENCES

def test_challenger_requires_independent_holdout_and_approval():
    champion = Evaluation("baseline", "new-held-out-bank", {"accuracy": .8, "calibration": .7}, True, True, 0)
    challenger = Evaluation("candidate", "new-held-out-bank", {"accuracy": .9, "calibration": .8}, False, True, 0)
    assert evaluate_challenger(champion, challenger).status == "hold"
    challenger = Evaluation("candidate", "new-held-out-bank", {"accuracy": .9, "calibration": .8}, True, True, 0)
    assert evaluate_challenger(champion, challenger).status == "hold"
    assert evaluate_challenger(champion, challenger, owner_approved=True).status == "eligible"

def test_regression_rejected():
    champion = Evaluation("baseline", "bank", {"accuracy": .8}, True, True, 0)
    challenger = Evaluation("candidate", "bank", {"accuracy": .7}, True, True, 0)
    assert evaluate_challenger(champion, challenger, owner_approved=True).status == "reject"
