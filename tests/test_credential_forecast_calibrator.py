from autonomous.credentials.intelligence.forecast_calibrator import (
    IntelligenceForecastCalibrator,
)


def test_calibration():

    result = IntelligenceForecastCalibrator().calibrate(
        [
            {
                "forecast": "continued_high_risk_pattern",
                "observed": "continued_high_risk_pattern",
            },
            {
                "forecast": "continued_high_risk_pattern",
                "observed": "other_pattern",
            },
        ]
    )

    assert result["forecast_accuracy"] == 0.5
    assert result["calibration"] == "moderate"
    assert result["mode"] == "read_only"
