from ai.factory.optimization_loop import (
    FactoryOptimizationLoop,
)


def test_optimal():
    loop = FactoryOptimizationLoop()

    result = loop.optimize(
        {
            "success_rate": 0.95,
        }
    )

    assert result["status"] == "OPTIMAL"
    assert result["action"] == "CONTINUE"


def test_degraded():
    loop = FactoryOptimizationLoop()

    result = loop.optimize(
        {
            "success_rate": 0.7,
        }
    )

    assert result["action"] == "IMPROVE"


def test_critical():
    loop = FactoryOptimizationLoop()

    result = loop.optimize(
        {
            "success_rate": 0.2,
        }
    )

    assert result["action"] == "RESTRUCTURE"


def test_history():
    loop = FactoryOptimizationLoop()

    loop.optimize(
        {
            "success_rate": 1,
        }
    )

    assert len(loop.history()) == 1
