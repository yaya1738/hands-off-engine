from ai.factory.alert_manager import (
    FactoryAlertManager,
)


def test_raise_alert():
    manager = FactoryAlertManager()

    alert = manager.raise_alert(
        "HEALTH_FAILURE",
        "scheduler",
    )

    assert alert["status"] == "ACTIVE"
    assert len(manager.active_alerts()) == 1


def test_resolve_alert():
    manager = FactoryAlertManager()

    manager.raise_alert(
        "FAILURE",
        "daemon",
    )

    result = manager.resolve_alert(
        "daemon"
    )

    assert result[0]["status"] == "RESOLVED"
    assert manager.active_alerts() == []


def test_history():
    manager = FactoryAlertManager()

    manager.raise_alert(
        "TEST",
        "runtime",
    )

    assert len(manager.history()) == 1
