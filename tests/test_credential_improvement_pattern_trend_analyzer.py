from autonomous.credentials.intelligence.improvement_pattern_trend_analyzer import (
    IntelligenceImprovementPatternTrendAnalyzer,
)


def test_trend():

    result = IntelligenceImprovementPatternTrendAnalyzer().analyze(
        {
            "pattern":
            "confidence_tracking_recurrence",
            "occurrences": 1,
            "confidence": 0.85,
        }
    )

    assert result["trend"] == "stable"
    assert result["occurrences"] == 1
    assert result["mode"] == "read_only"
