from ai.factory.optimization_executor import (
    FactoryOptimizationExecutor,
)


def test_execute_improvement():
    executor = FactoryOptimizationExecutor()

    executor.register_action(
        "IMPROVE",
        lambda: "tuned",
    )

    result = executor.execute(
        {
            "action": "IMPROVE",
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["output"] == "tuned"


def test_missing_action():
    executor = FactoryOptimizationExecutor()

    result = executor.execute(
        {
            "action": "UNKNOWN",
        }
    )

    assert result["status"] == "NO_HANDLER"


def test_history():
    executor = FactoryOptimizationExecutor()

    executor.execute(
        {
            "action": "UNKNOWN",
        }
    )

    assert len(executor.history()) == 1
