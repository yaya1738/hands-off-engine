from ai.factory.task_queue import FactoryTaskQueue


def test_add_and_get_task():
    queue = FactoryTaskQueue()

    queue.add_task(
        "task-001",
        "build module",
    )

    task = queue.next_task()

    assert task["task_id"] == "task-001"
    assert task["status"] == "RUNNING"


def test_complete_task():
    queue = FactoryTaskQueue()

    queue.add_task(
        "task-002",
        "test queue",
    )

    queue.complete_task(
        "task-002",
        {
            "status": "SUCCESS",
        },
    )

    task = queue.list_tasks()[0]

    assert task["status"] == "COMPLETE"
    assert task["result"]["status"] == "SUCCESS"


def test_empty_queue():
    queue = FactoryTaskQueue()

    assert queue.next_task() is None
