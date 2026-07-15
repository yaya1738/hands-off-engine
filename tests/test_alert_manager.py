from ai.factory.alert_manager import (
    FactoryAlertManager,
)


def test_critical_alert():
    manager = FactoryAlertManager()

    result = manager.create_alert(
        "failure"
    )

    assert result["level"] == "CRITICAL"


def test_warning_alert():
    manager = FactoryAlertManager()

    result = manager.create_alert(
        "degraded"
    )

    assert result["level"] == "WARNING"


def test_info_alert():
    manager = FactoryAlertManager()

    result = manager.create_alert(
        "notice"
    )

    assert result["level"] == "INFO"


def test_history():
    manager = FactoryAlertManager()

    manager.create_alert(
        "failure"
    )

    assert len(manager.history()) == 1
