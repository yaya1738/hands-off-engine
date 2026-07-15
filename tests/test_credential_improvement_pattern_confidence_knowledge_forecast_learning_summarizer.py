from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_learning_summarizer import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningSummarizer,
)


def test_summary():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningSummarizer().summarize(
        [
            {
                "knowledge":
                "forecast_feedback_consolidated",
                "score":
                1.0,
            }
        ]
    )

    assert result["summary"] == (
        "forecast_feedback_consolidated"
    )
    assert result["confidence"] == 1.0
    assert result["mode"] == "read_only"
