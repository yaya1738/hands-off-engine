from ai.factory.strategy_manager import (
    FactoryStrategyManager,
)


def build():
    return FactoryStrategyManager()


def test_registry():
    engine = build()

    result = engine.strategy_registry(
        "default",
        {},
    )

    assert result["registered"] is True


def test_evaluate():
    engine = build()

    result = engine.evaluate_strategy(
        "default",
    )

    assert result["evaluated"] is True


def test_activate():
    engine = build()

    result = engine.activate_strategy(
        "default",
    )

    assert result["activated"] is True


def test_retire():
    engine = build()

    result = engine.retire_strategy(
        "default",
    )

    assert result["retired"] is True


def test_performance():
    engine = build()

    result = engine.strategy_performance(
        "default",
    )

    assert result["measured"] is True


def test_history():
    engine = build()

    engine.activate_strategy(
        "default",
    )

    assert len(engine.history()) == 1
