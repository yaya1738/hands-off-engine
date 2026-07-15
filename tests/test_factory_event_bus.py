from ai.factory.event_bus import FactoryEventBus


def test_publish_event():
    bus = FactoryEventBus()

    received = []

    def handler(payload):
        received.append(payload)

    bus.subscribe(
        "task_complete",
        handler,
    )

    bus.publish(
        "task_complete",
        {
            "task_id": "001",
        },
    )

    assert received[0]["task_id"] == "001"


def test_event_history():
    bus = FactoryEventBus()

    bus.publish(
        "artifact_created",
        {
            "id": "a1",
        },
    )

    assert len(bus.history()) == 1
    assert bus.history()[0]["type"] == "artifact_created"
