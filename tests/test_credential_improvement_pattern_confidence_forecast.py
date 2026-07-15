from autonomous.credentials.intelligence.improvement_pattern_confidence_forecast import (
    IntelligenceImprovementPatternConfidenceForecast,
)


def test_forecast():

    result = IntelligenceImprovementPatternConfidenceForecast().forecast(
        {
            "trend":
            "stable",
            "confidence":
            0.85,
        }
    )

    assert result["forecast"] == (
        "continued_stability"
    )
    assert result["confidence"] == 0.82
    assert result["mode"] == "read_only"
