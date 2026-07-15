from ai.factory.event_log import FactoryEventLog


def test_event_recording():
    log = FactoryEventLog()

    log.record(
        "BUILD_COMPLETE",
        {
            "task_id": "factory-001",
        },
    )

    events = log.all()

    assert len(events) == 1
    assert events[0]["event_type"] == "BUILD_COMPLETE"
    assert events[0]["data"]["task_id"] == "factory-001"
