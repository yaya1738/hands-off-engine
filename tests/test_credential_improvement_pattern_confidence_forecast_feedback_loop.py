from autonomous.credentials.intelligence.improvement_pattern_confidence_forecast_feedback_loop import (
    IntelligenceImprovementPatternConfidenceForecastFeedbackLoop,
)


def test_feedback():

    result = IntelligenceImprovementPatternConfidenceForecastFeedbackLoop().record(
        {
            "forecast_accuracy":
            1.0
        }
    )

    assert result["feedback"] == (
        "forecast_calibration_recorded"
    )
    assert result["accuracy"] == 1.0
    assert result["learning_updated"] is True
    assert result["mode"] == "read_only"
