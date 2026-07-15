from autonomous.credentials.intelligence.anomaly_detector import (
    IntelligenceAnomalyDetector,
)


def test_anomaly():

    result = IntelligenceAnomalyDetector().detect(
        0.69,
        0.81,
    )

    assert result["anomaly_detected"] is True
    assert result["type"] == "confidence_shift"
    assert result["severity"] == "medium"
    assert result["mode"] == "read_only"
