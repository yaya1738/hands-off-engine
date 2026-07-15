from autonomous.credentials.intelligence.pattern_forecast_engine import (
    IntelligencePatternForecastEngine,
)


def test_forecast():

    result = IntelligencePatternForecastEngine().forecast(
        {
            "pattern": "repeated_high_risk_attention",
            "trend": "increasing",
            "confidence": 0.86,
        }
    )

    assert result["forecast"] == "continued_high_risk_pattern"
    assert result["confidence"] == 0.82
    assert result["mode"] == "read_only"
