from ai.factory.optimization_intelligence import (
    FactoryOptimizationIntelligence,
)


def build():
    return FactoryOptimizationIntelligence()


def test_measure_performance():
    engine = build()

    result = engine.measure_performance(
        {}
    )

    assert result["measured"] is True


def test_identify_improvement():
    engine = build()

    result = engine.identify_improvement(
        {}
    )

    assert result["identified"] is True


def test_optimize_process():
    engine = build()

    result = engine.optimize_process(
        {}
    )

    assert result["optimized"] is True


def test_compare_results():
    engine = build()

    result = engine.compare_results(
        {},
        {},
    )

    assert result["compared"] is True


def test_history():
    engine = build()

    engine.optimize_process(
        {}
    )

    assert len(engine.history()) == 1
