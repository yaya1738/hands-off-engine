from ai.factory.maintenance_executor import (
    FactoryMaintenanceExecutor,
)


def test_execute_action():
    executor = FactoryMaintenanceExecutor()

    executor.register_action(
        "RUN_CHECK",
        lambda: "checked",
    )

    result = executor.execute(
        {
            "action": "RUN_CHECK",
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["output"] == "checked"


def test_missing_action():
    executor = FactoryMaintenanceExecutor()

    result = executor.execute(
        {
            "action": "UNKNOWN",
        }
    )

    assert result["status"] == "NO_HANDLER"


def test_history():
    executor = FactoryMaintenanceExecutor()

    executor.execute(
        {
            "action": "UNKNOWN",
        }
    )

    assert len(executor.history()) == 1
