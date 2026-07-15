from autonomous.credentials.intelligence.regression_detector import (
    RegressionDetector,
)


def test_regression():

    result = RegressionDetector().analyze(
        [
            {
                "confidence": 0.83
            },
            {
                "confidence": 0.55
            },
        ]
    )

    assert result["regression_detected"] is True
    assert result["reason"] == "confidence_drop"
    assert result["mode"] == "read_only"
