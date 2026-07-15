from ai.factory.master_integration import (
    FactoryMasterIntegration,
)


def build():
    return FactoryMasterIntegration()


def test_register_component():
    factory = build()

    result = factory.register_component(
        "state",
        {}
    )

    assert result["registered"] is True


def test_initialize_system():
    factory = build()

    result = factory.initialize_system()

    assert result["initialized"] is True


def test_run_cycle():
    factory = build()

    result = factory.run_cycle()

    assert result["ran"] is True


def test_get_system_status():
    factory = build()

    result = factory.get_system_status()

    assert "initialized" in result


def test_history():
    factory = build()

    factory.run_cycle()

    assert len(factory.history()) == 1
