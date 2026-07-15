from ai.factory.improvement_executor import (
    FactoryImprovementExecutor,
)


def test_block_unapproved():
    executor = FactoryImprovementExecutor()

    result = executor.execute(
        {
            "status": "PENDING",
        },
        lambda: "done",
    )

    assert result["status"] == "BLOCKED"


def test_execute_approved():
    executor = FactoryImprovementExecutor()

    result = executor.execute(
        {
            "status": "APPROVED",
        },
        lambda: "done",
    )

    assert result["status"] == "EXECUTED"
    assert result["output"] == "done"


def test_failed_execution():
    executor = FactoryImprovementExecutor()

    result = executor.execute(
        {
            "status": "APPROVED",
        },
        lambda: 1 / 0,
    )

    assert result["status"] == "FAILED"


def test_history():
    executor = FactoryImprovementExecutor()

    executor.execute(
        {
            "status": "PENDING",
        },
        lambda: "done",
    )

    assert len(executor.history()) == 1
