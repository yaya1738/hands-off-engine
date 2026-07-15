from ai.factory.job_executor import (
    FactoryJobExecutor,
)


def test_register_and_execute():
    executor = FactoryJobExecutor()

    executor.register_handler(
        "snapshot",
        lambda payload: {
            "created": True,
        },
    )

    result = executor.execute(
        "snapshot"
    )

    assert result["created"] is True


def test_unknown_job():
    executor = FactoryJobExecutor()

    result = executor.execute(
        "missing"
    )

    assert result["error"] == "unknown_job"


def test_available_jobs():
    executor = FactoryJobExecutor()

    executor.register_handler(
        "optimize",
        lambda payload: None,
    )

    assert "optimize" in executor.available_jobs()
