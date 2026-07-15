from ai.factory.supervisor import (
    FactorySupervisor,
)


def build():
    return FactorySupervisor()


def test_register_component():
    supervisor = build()

    result = supervisor.register_component(
        "engine",
        {},
    )

    assert result["registered"] is True


def test_check_status():
    supervisor = build()

    result = supervisor.check_status()

    assert result["healthy"] is True


def test_coordinate_cycle():
    supervisor = build()

    result = supervisor.coordinate_cycle(
        {}
    )

    assert result["coordinated"] is True


def test_trigger_recovery():
    supervisor = build()

    result = supervisor.trigger_recovery(
        {}
    )

    assert result["recovery_triggered"] is True


def test_history():
    supervisor = build()

    supervisor.check_status()

    assert len(supervisor.history()) == 1
