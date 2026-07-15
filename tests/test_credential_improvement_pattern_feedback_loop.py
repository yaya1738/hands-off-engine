from autonomous.credentials.intelligence.improvement_pattern_feedback_loop import (
    IntelligenceImprovementPatternFeedbackLoop,
)


def test_feedback():

    result = IntelligenceImprovementPatternFeedbackLoop().record(
        {
            "forecast_accuracy": 1.0,
        }
    )

    assert result["feedback"] == (
        "forecast_calibration_recorded"
    )
    assert result["accuracy"] == 1.0
    assert result["learning_updated"] is True
    assert result["mode"] == "read_only"
