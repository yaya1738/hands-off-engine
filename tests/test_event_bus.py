from ai.factory.event_bus import (
    FactoryEventBus,
)


def test_publish_event():
    bus = FactoryEventBus()

    result = bus.publish(
        "JOB_COMPLETED",
        {
            "status": "SUCCESS",
        },
    )

    assert result == []
    assert bus.history()[0]["event"] == "JOB_COMPLETED"


def test_subscriber_receives_event():
    bus = FactoryEventBus()

    received = []

    def handler(payload):
        received.append(payload)
        return "ok"

    bus.subscribe(
        "JOB_COMPLETED",
        handler,
    )

    result = bus.publish(
        "JOB_COMPLETED",
        {
            "id": 1,
        },
    )

    assert received[0]["id"] == 1
    assert result[0] == "ok"


def test_history():
    bus = FactoryEventBus()

    bus.publish(
        "TEST",
    )

    assert len(bus.history()) == 1
