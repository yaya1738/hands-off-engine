from ai.factory.simulation_intelligence import (
    FactorySimulationIntelligence,
)


def build():
    return FactorySimulationIntelligence()


def test_create_scenario():
    engine = build()

    result = engine.create_scenario(
        {}
    )

    assert result["created"] is True


def test_run_simulation():
    engine = build()

    result = engine.run_simulation(
        {}
    )

    assert result["simulated"] is True


def test_compare_outcomes():
    engine = build()

    result = engine.compare_outcomes(
        []
    )

    assert result["compared"] is True


def test_select_scenario():
    engine = build()

    result = engine.select_scenario(
        []
    )

    assert result["selected"] is True


def test_history():
    engine = build()

    engine.create_scenario(
        {}
    )

    assert len(engine.history()) == 1
