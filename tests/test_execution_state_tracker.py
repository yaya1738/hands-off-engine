from ai.factory.execution_state_tracker import (
    FactoryExecutionStateTracker,
)


def build():
    return FactoryExecutionStateTracker()


def test_create_execution():
    tracker = build()

    result = tracker.create_execution(
        {
            "action": "RUN",
        }
    )

    assert result["status"] == "PLANNED"


def test_update_status():
    tracker = build()

    execution = tracker.create_execution({})

    result = tracker.update_status(
        execution,
        "RUNNING",
    )

    assert result["status"] == "RUNNING"


def test_get_state():
    tracker = build()

    execution = tracker.create_execution({})

    result = tracker.get_state(
        execution
    )

    assert result["status"] == "PLANNED"


def test_completed():
    tracker = build()

    execution = tracker.create_execution({})

    tracker.update_status(
        execution,
        "COMPLETED",
    )

    result = tracker.get_state(
        execution
    )

    assert result["status"] == "COMPLETED"


def test_history():
    tracker = build()

    tracker.create_execution({})

    assert len(tracker.history()) == 1
