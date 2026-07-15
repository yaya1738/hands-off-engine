from ai.factory.strategy_evolution import (
    FactoryStrategyEvolution,
)


def build():
    return FactoryStrategyEvolution()


def test_store_strategy():
    engine = build()

    result = engine.store_strategy(
        {
            "name": "A",
        }
    )

    assert result["stored"] is True


def test_evaluate_strategy():
    engine = build()

    result = engine.evaluate_strategy(
        {}
    )

    assert result["evaluated"] is True


def test_evolve_strategy():
    engine = build()

    result = engine.evolve_strategy(
        {}
    )

    assert result["evolved"] is True


def test_select_strategy():
    engine = build()

    engine.store_strategy(
        {
            "id": 1,
        }
    )

    result = engine.select_strategy()

    assert result["selected"]["id"] == 1


def test_history():
    engine = build()

    engine.store_strategy({})

    assert len(engine.history()) == 1
