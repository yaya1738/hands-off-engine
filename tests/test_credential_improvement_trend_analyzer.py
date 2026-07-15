from autonomous.credentials.intelligence.improvement_trend_analyzer import (
    IntelligenceImprovementTrendAnalyzer,
)


def test_trend():

    result = IntelligenceImprovementTrendAnalyzer().analyze(
        [
            {
                "improvement_id": "increase_pattern_confidence_tracking",
                "occurrences": 1,
            }
        ]
    )

    assert result["trend"] == "stable"
    assert result["occurrences"] == 1
    assert result["mode"] == "read_only"
