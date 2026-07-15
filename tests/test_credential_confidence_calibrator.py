from autonomous.credentials.intelligence.confidence_calibrator import (
    IntelligenceConfidenceCalibrator,
)


def test_calibration():

    result = IntelligenceConfidenceCalibrator().calibrate(
        [
            {
                "forecast": "degraded",
                "observed": "degraded",
            },
            {
                "forecast": "stable",
                "observed": "stable",
            },
            {
                "forecast": "degraded",
                "observed": "stable",
            },
        ]
    )

    assert result["forecast_accuracy"] == 0.67
    assert result["mode"] == "read_only"
