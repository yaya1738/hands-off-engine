from autonomous.credentials.intelligence.improvement_confidence_calibrator import (
    IntelligenceImprovementConfidenceCalibrator,
)


def test_calibration():

    result = IntelligenceImprovementConfidenceCalibrator().calibrate(
        [
            {
                "correct": True,
            }
        ]
    )

    assert result["forecast_accuracy"] == 1.0
    assert result["calibration"] == "good"
    assert result["observations"] == 1
    assert result["mode"] == "read_only"
