from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_trend_analyzer import (
    IntelligenceImprovementPatternConfidenceKnowledgeTrendAnalyzer,
)


def test_trend():

    result = IntelligenceImprovementPatternConfidenceKnowledgeTrendAnalyzer().analyze(
        [
            {
                "knowledge":
                "forecast_feedback_consolidated",
                "confidence":
                1.0,
            }
        ]
    )

    assert result["trend"] == "stable"
    assert result["knowledge"] == (
        "forecast_feedback_consolidated"
    )
    assert result["confidence"] == 1.0
    assert result["mode"] == "read_only"
