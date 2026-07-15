from autonomous.credentials.intelligence.improvement_pattern_forecast_calibrator import (
    IntelligenceImprovementPatternForecastCalibrator,
)


def test_calibration():

    result = IntelligenceImprovementPatternForecastCalibrator().calibrate(
        "continued_confidence_tracking_pattern",
        "continued_confidence_tracking_pattern",
    )

    assert result["forecast_accuracy"] == 1.0
    assert result["calibration"] == "good"
    assert result["mode"] == "read_only"
