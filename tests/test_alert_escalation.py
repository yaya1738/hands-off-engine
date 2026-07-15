from ai.factory.alert_escalation import (
    FactoryAlertEscalation,
)


def test_escalate():
    manager = FactoryAlertEscalation()

    manager.register_handler(
        "RECOVER",
        lambda alert: "restarted",
    )

    result = manager.escalate(
        {
            "action": "RECOVER",
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["output"] == "restarted"


def test_missing_handler():
    manager = FactoryAlertEscalation()

    result = manager.escalate(
        {
            "action": "UNKNOWN",
        }
    )

    assert result["status"] == "NO_HANDLER"


def test_resolve():
    manager = FactoryAlertEscalation()

    result = manager.resolve(
        {
            "issue": "failure",
        }
    )

    assert result["status"] == "RESOLVED"


def test_history():
    manager = FactoryAlertEscalation()

    manager.resolve(
        {
            "issue": "test",
        }
    )

    assert len(manager.history()) == 1
