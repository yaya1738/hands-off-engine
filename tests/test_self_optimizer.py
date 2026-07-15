from ai.factory.self_optimizer import (
    FactorySelfOptimizer,
)


def test_needs_optimization():
    optimizer = FactorySelfOptimizer()

    result = optimizer.optimize(
        {
            "success_rate": 0.5,
        }
    )

    assert (
        result["evaluation"]["status"]
        == "NEEDS_OPTIMIZATION"
    )


def test_good():
    optimizer = FactorySelfOptimizer()

    result = optimizer.optimize(
        {
            "success_rate": 1,
        }
    )

    assert (
        result["action"]["action"]
        == "MAINTAIN"
    )


def test_tune():
    optimizer = FactorySelfOptimizer()

    result = optimizer.tune(
        "threshold",
        0.9,
    )

    assert result["value"] == 0.9


def test_history():
    optimizer = FactorySelfOptimizer()

    optimizer.evaluate({})

    assert len(optimizer.history()) == 1
