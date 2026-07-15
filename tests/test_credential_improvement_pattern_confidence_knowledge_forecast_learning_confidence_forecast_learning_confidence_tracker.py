from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_learning_confidence_forecast_learning_confidence_tracker import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceTracker,
)


def test_track():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceTracker().track(
        {
            "summary":
            "forecast_feedback_consolidated",
            "confidence":
            1.0,
        }
    )

    assert result["knowledge"] == (
        "forecast_feedback_consolidated"
    )
    assert result["confidence"] == 1.0
    assert result["history_entries"] == 1
    assert result["mode"] == "read_only"
