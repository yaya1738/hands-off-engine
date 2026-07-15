from ai.factory.build_task import BuildTask


def test_task_completion():
    task = BuildTask(
        task_id="factory-001",
        description="Create build task model",
    )

    task.complete()

    assert task.status == "COMPLETED"


def test_task_failure():
    task = BuildTask(
        task_id="factory-002",
        description="Test failure handling",
    )

    task.fail("test_failed")

    assert task.status == "FAILED"
    assert "test_failed" in task.changes
