from ai.factory.optimization_context import (
    OptimizationContext,
)


def test_context_build():
    context = OptimizationContext()

    result = context.build(
        {
            "status": "HEALTHY",
        },
        {
            "tasks_total": 10,
        },
        [
            {
                "event": "run",
            }
        ],
        {
            "mode": "active",
        },
    )

    assert result["health"]["status"] == "HEALTHY"
    assert result["metrics"]["tasks_total"] == 10
    assert result["state"]["mode"] == "active"


def test_context_contains_history():
    context = OptimizationContext()

    result = context.build(
        {},
        {},
        ["event"],
        {},
    )

    assert len(result["history"]) == 1
