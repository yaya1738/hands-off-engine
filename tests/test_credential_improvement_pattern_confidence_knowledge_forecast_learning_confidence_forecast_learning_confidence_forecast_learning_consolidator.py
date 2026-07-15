from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_learning_confidence_forecast_learning_confidence_forecast_learning_consolidator import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceForecastLearningConfidenceForecastLearningConsolidator,
)


def test_consolidate():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceForecastLearningConfidenceForecastLearningConsolidator().consolidate(
        {
            "accuracy":
            1.0
        }
    )

    assert result["learning_event"] == (
        "forecast_feedback_consolidated"
    )
    assert result["reliability"] == 1.0
    assert result["memory_updated"] is True
    assert result["mode"] == "read_only"
