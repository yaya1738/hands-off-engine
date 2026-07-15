from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_calibrator import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastCalibrator,
)


def test_calibration():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastCalibrator().calibrate(
        [
            {
                "forecast":
                "continued_stability",
                "outcome":
                "continued_stability",
            }
        ]
    )

    assert result["forecast_accuracy"] == 1.0
    assert result["calibration"] == "good"
    assert result["observations"] == 1
    assert result["mode"] == "read_only"
