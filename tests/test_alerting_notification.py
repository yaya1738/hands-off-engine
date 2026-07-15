from ai.factory.alerting_notification import (
    FactoryAlertingNotification,
)


def build():
    return FactoryAlertingNotification()


def test_create_alert():
    alerts = build()

    result = alerts.create_alert(
        {
            "type": "ERROR",
        }
    )

    assert result["created"] is True


def test_evaluate_condition():
    alerts = build()

    result = alerts.evaluate_condition(
        {}
    )

    assert result["evaluated"] is True


def test_send_notification():
    alerts = build()

    result = alerts.send_notification(
        {
            "message": "test",
        }
    )

    assert result["sent"] is True


def test_resolve_alert():
    alerts = build()

    result = alerts.resolve_alert(
        {}
    )

    assert result["resolved"] is True


def test_history():
    alerts = build()

    alerts.create_alert({})

    assert len(alerts.history()) == 1
