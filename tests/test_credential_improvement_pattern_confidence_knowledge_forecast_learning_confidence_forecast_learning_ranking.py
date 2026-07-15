from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_learning_confidence_forecast_learning_ranking import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRanking,
)


def test_rank():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRanking().rank(
        [
            {
                "learning_event":
                "forecast_feedback_consolidated",
                "reliability":
                1.0,
            }
        ]
    )

    assert result["ranking"][0]["knowledge"] == (
        "forecast_feedback_consolidated"
    )
    assert result["ranking"][0]["score"] == 1.0
    assert result["mode"] == "read_only"
