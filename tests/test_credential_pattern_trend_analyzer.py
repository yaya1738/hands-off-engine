from autonomous.credentials.intelligence.pattern_trend_analyzer import (
    IntelligencePatternTrendAnalyzer,
)


def test_trend():

    result = IntelligencePatternTrendAnalyzer().analyse(
        [
            {
                "pattern_id": "repeated_high_risk_attention",
                "occurrences": 1,
            },
            {
                "pattern_id": "repeated_high_risk_attention",
                "occurrences": 3,
            },
        ]
    )

    assert result["trend"] == "increasing"
    assert result["confidence"] == 0.86
    assert result["mode"] == "read_only"
