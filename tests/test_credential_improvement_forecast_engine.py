from autonomous.credentials.intelligence.improvement_forecast_engine import (
    IntelligenceImprovementForecastEngine,
)


def test_forecast():

    result = IntelligenceImprovementForecastEngine().forecast(
        {
            "trend": "stable",
        }
    )

    assert result["forecast"] == "continued_confidence_tracking_need"
    assert result["confidence"] == 0.80
    assert result["mode"] == "read_only"
