from ai.factory.improvement_queue import (
    FactoryImprovementQueue,
)


def test_enqueue():
    queue = FactoryImprovementQueue()

    result = queue.enqueue(
        {
            "name": "optimize",
        }
    )

    assert result["status"] == "PENDING"


def test_dequeue():
    queue = FactoryImprovementQueue()

    queue.enqueue(
        {
            "name": "optimize",
        }
    )

    result = queue.dequeue()

    assert result["status"] == "RUNNING"


def test_complete():
    queue = FactoryImprovementQueue()

    item = queue.enqueue(
        {
            "name": "optimize",
        }
    )

    queue.dequeue()

    result = queue.complete(
        item,
        {
            "success": True,
        },
    )

    assert result["status"] == "COMPLETE"


def test_pending():
    queue = FactoryImprovementQueue()

    queue.enqueue(
        {
            "name": "test",
        }
    )

    assert len(queue.pending()) == 1


def test_history():
    queue = FactoryImprovementQueue()

    queue.enqueue(
        {
            "name": "test",
        }
    )

    assert len(queue.history()) == 1
