from ai.factory.incident_manager import (
    FactoryIncidentManager,
)


def test_create():
    manager = FactoryIncidentManager()

    result = manager.create(
        "scheduler_failure",
        "CRITICAL",
    )

    assert result["status"] == "OPEN"
    assert result["severity"] == "CRITICAL"


def test_update():
    manager = FactoryIncidentManager()

    incident = manager.create(
        "test",
    )

    result = manager.update(
        incident,
        "RECOVERING",
    )

    assert result["status"] == "RECOVERING"


def test_close():
    manager = FactoryIncidentManager()

    incident = manager.create(
        "test",
    )

    result = manager.close(
        incident,
        "restart fixed issue",
    )

    assert result["status"] == "CLOSED"
    assert result["lesson"] == "restart fixed issue"


def test_history():
    manager = FactoryIncidentManager()

    manager.create(
        "test",
    )

    assert len(manager.history()) == 1
