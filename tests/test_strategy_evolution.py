from ai.factory.strategy_evolution import (
    FactoryStrategyEvolution,
)


def build():
    return FactoryStrategyEvolution()


def test_register_strategy():
    engine = build()

    result = engine.register_strategy(
        "A",
        {}
    )

    assert result["registered"] is True


def test_evaluate_strategy():
    engine = build()

    result = engine.evaluate_strategy(
        "A",
        {}
    )

    assert result["evaluated"] is True


def test_replace_strategy():
    engine = build()

    result = engine.replace_strategy(
        "A",
        "B",
    )

    assert result["replaced"] is True


def test_activate_strategy():
    engine = build()

    result = engine.activate_strategy(
        "B"
    )

    assert result["activated"] is True


def test_history():
    engine = build()

    engine.register_strategy(
        "A",
        {}
    )

    assert len(engine.history()) == 1
