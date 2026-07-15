from autonomous.credentials.intelligence.improvement_pattern_forecast_engine import (
    IntelligenceImprovementPatternForecastEngine,
)


def test_forecast():

    result = IntelligenceImprovementPatternForecastEngine().forecast(
        {
            "pattern":
            "confidence_tracking_recurrence",
            "trend":
            "stable",
        }
    )

    assert result["forecast"] == (
        "continued_confidence_tracking_pattern"
    )
    assert result["confidence"] == 0.82
    assert result["mode"] == "read_only"
