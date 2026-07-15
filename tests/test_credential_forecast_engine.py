from autonomous.credentials.intelligence.forecast_engine import (
    IntelligenceForecastEngine,
)


def test_forecast():

    result = IntelligenceForecastEngine().forecast(
        "declining",
        "degraded",
        0.55,
    )

    assert result["forecast"] == "continued_degradation_risk"
    assert result["mode"] == "read_only"
