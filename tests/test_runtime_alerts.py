from ai.factory.runtime_alerts import (
    FactoryRuntimeAlerts,
)


def test_down_alert():
    alerts = FactoryRuntimeAlerts()

    result = alerts.check(
        {
            "status": "DOWN",
        }
    )

    assert result["level"] == "CRITICAL"


def test_degraded_alert():
    alerts = FactoryRuntimeAlerts()

    result = alerts.check(
        {
            "status": "DEGRADED",
        }
    )

    assert result["level"] == "WARNING"


def test_healthy_alert():
    alerts = FactoryRuntimeAlerts()

    result = alerts.check(
        {
            "status": "HEALTHY",
        }
    )

    assert result["level"] == "INFO"


def test_history():
    alerts = FactoryRuntimeAlerts()

    alerts.check(
        {
            "status": "DOWN",
        }
    )

    assert len(alerts.history()) == 1
