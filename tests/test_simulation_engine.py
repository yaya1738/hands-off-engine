from ai.factory.simulation_engine import (
    FactorySimulationEngine,
)


def build():
    return FactorySimulationEngine()


def test_create_scenario():
    engine = build()

    result = engine.create_scenario(
        {
            "name": "TEST",
        }
    )

    assert result["created"] is True


def test_simulate_action():
    engine = build()

    result = engine.simulate_action(
        {
            "action": "RUN",
        }
    )

    assert result["simulated"] is True


def test_evaluate_result():
    engine = build()

    result = engine.evaluate_result(
        {}
    )

    assert result["evaluated"] is True


def test_compare_outcomes():
    engine = build()

    result = engine.compare_outcomes(
        {},
        {},
    )

    assert result["compared"] is True


def test_history():
    engine = build()

    engine.create_scenario({})

    assert len(engine.history()) == 1
