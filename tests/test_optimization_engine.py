from ai.factory.optimization_engine import (
    FactoryOptimizationEngine,
)


def build():
    return FactoryOptimizationEngine()


def test_collect_signals():
    engine = build()

    result = engine.collect_signals(
        {
            "metric": "speed",
        }
    )

    assert result["collected"] is True


def test_optimize():
    engine = build()

    result = engine.optimize()

    assert result["optimized"] is True


def test_compare_versions():
    engine = build()

    result = engine.compare_versions(
        {},
        {},
    )

    assert result["compared"] is True


def test_recommend_improvement():
    engine = build()

    engine.collect_signals({})

    result = engine.recommend_improvement()

    assert result["recommendation"] == "IMPROVE"


def test_history():
    engine = build()

    engine.optimize()

    assert len(engine.history()) == 1
