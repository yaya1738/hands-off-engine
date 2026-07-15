from autonomous.credentials.intelligence.calibration import (
    ConfidenceCalibrator,
)


def test_calibration_reduces_uncertainty():

    result = ConfidenceCalibrator().calibrate(
        1.0,
        5
    )

    assert result["calibrated_confidence"] < 1.0
    assert result["mode"] == "read_only"
