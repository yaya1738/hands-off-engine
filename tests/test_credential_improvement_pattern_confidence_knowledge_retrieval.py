from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_retrieval import (
    IntelligenceImprovementPatternConfidenceKnowledgeRetrieval,
)


def test_retrieval():

    result = IntelligenceImprovementPatternConfidenceKnowledgeRetrieval().query(
        "forecast_feedback_consolidated",
        [
            {
                "learning_event":
                "forecast_feedback_consolidated"
            }
        ],
    )

    assert result["query"] == (
        "forecast_feedback_consolidated"
    )
    assert result["matches"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
