from autonomous.credentials.intelligence.forecast_feedback_loop import (
    IntelligenceForecastFeedbackLoop,
)


def test_feedback():

    loop = IntelligenceForecastFeedbackLoop()

    result = loop.record(
        {
            "forecast": "continued_high_risk_pattern"
        }
    )

    assert result["feedback"] == "forecast_recorded"
    assert result["outcome"] == "pending"
    assert result["mode"] == "read_only"
