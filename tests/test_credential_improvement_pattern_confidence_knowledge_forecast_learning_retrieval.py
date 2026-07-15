from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_learning_retrieval import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRetrieval,
)


def test_query():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRetrieval().query(
        "forecast_feedback_consolidated",
        [
            {
                "learning_event":
                "forecast_feedback_consolidated",
                "reliability":
                1.0,
            }
        ],
    )

    assert result["query"] == (
        "forecast_feedback_consolidated"
    )
    assert result["matches"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
