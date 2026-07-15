from ai.factory.strategy_evolution_intelligence import (
    FactoryStrategyEvolutionIntelligence,
)


def build():
    return FactoryStrategyEvolutionIntelligence()


def test_register_strategy():
    engine = build()

    result = engine.register_strategy(
        {}
    )

    assert result["registered"] is True


def test_evaluate_strategy():
    engine = build()

    result = engine.evaluate_strategy(
        {}
    )

    assert result["evaluated"] is True


def test_select_strategy():
    engine = build()

    result = engine.select_strategy(
        []
    )

    assert result["selected"] is True


def test_evolve_strategy():
    engine = build()

    result = engine.evolve_strategy(
        {}
    )

    assert result["evolved"] is True


def test_history():
    engine = build()

    engine.register_strategy(
        {}
    )

    assert len(engine.history()) == 1
