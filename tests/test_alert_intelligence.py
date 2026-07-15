from ai.factory.alert_intelligence import (
    FactoryAlertIntelligence,
)


def build():
    return FactoryAlertIntelligence()


def test_create_alert():
    engine = build()

    result = engine.create_alert(
        {}
    )

    assert result["created"] is True


def test_evaluate_alert():
    engine = build()

    result = engine.evaluate_alert(
        {}
    )

    assert result["evaluated"] is True


def test_escalate_alert():
    engine = build()

    result = engine.escalate_alert(
        {}
    )

    assert result["escalated"] is True


def test_resolve_alert():
    engine = build()

    result = engine.resolve_alert(
        {}
    )

    assert result["resolved"] is True


def test_history():
    engine = build()

    engine.create_alert(
        {}
    )

    assert len(engine.history()) == 1
