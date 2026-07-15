from ai.factory.optimization_engine import (
    FactoryOptimizationEngine,
)


def build():
    return FactoryOptimizationEngine()


def test_evaluate_options():
    engine = build()

    result = engine.evaluate_options(
        []
    )

    assert result["evaluated"] is True


def test_rank_improvements():
    engine = build()

    result = engine.rank_improvements(
        []
    )

    assert result["ranked"] is True


def test_apply_optimization():
    engine = build()

    result = engine.apply_optimization(
        {}
    )

    assert result["applied"] is True


def test_measure_gain():
    engine = build()

    result = engine.measure_gain(
        {},
        {},
    )

    assert result["measured"] is True


def test_history():
    engine = build()

    engine.apply_optimization({})

    assert len(engine.history()) == 1
