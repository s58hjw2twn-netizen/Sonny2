import pytest
from sonny.self_model_research import SelfPrediction, calibration_metrics


def test_calibration_is_measurable_not_consciousness():
    result = calibration_metrics([
        SelfPrediction("trial-1", 0.9, True, "digest-a"),
        SelfPrediction("trial-2", 0.2, False, "digest-b")])
    assert result["sample_size"] == 2
    assert result["brier_score"] == pytest.approx(0.025)
    assert result["subjective_consciousness_established"] is False


def test_missing_evidence_rejected():
    with pytest.raises(ValueError):
        calibration_metrics([SelfPrediction("trial-1", 0.5, True, "")])


def test_empty_not_success():
    assert calibration_metrics([])["status"] == "INSUFFICIENT_DATA"
