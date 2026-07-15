from autonomous.credentials.intelligence.alert_composer import (
    AlertComposer,
)


def test_alert():

    result = AlertComposer().compose(
        {
            "regression_detected": True,
            "reason": "confidence_drop",
            "previous_confidence": 0.83,
            "current_confidence": 0.55,
        }
    )

    assert result["alert_level"] == "warning"
    assert result["mode"] == "read_only"
