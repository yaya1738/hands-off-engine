from autonomous.credentials.intelligence.improvement_pattern_confidence_trend_analyzer import (
    IntelligenceImprovementPatternConfidenceTrendAnalyzer,
)


def test_trend():

    result = IntelligenceImprovementPatternConfidenceTrendAnalyzer().analyze(
        [
            {
                "pattern":
                "prioritize_pattern_feedback_learning",
                "confidence":
                0.85,
            }
        ]
    )

    assert result["trend"] == "stable"
    assert result["pattern"] == (
        "prioritize_pattern_feedback_learning"
    )
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
