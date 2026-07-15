from ai.factory.event_processing import (
    FactoryEventProcessing,
)


def build():
    return FactoryEventProcessing()


def test_publish_event():
    bus = build()

    result = bus.publish_event(
        {
            "type": "UPDATE",
        }
    )

    assert result["published"] is True


def test_subscribe():
    bus = build()

    result = bus.subscribe(
        "UPDATE",
        lambda x: x,
    )

    assert result["subscribed"] is True


def test_process_events():
    bus = build()

    bus.publish_event({})

    result = bus.process_events()

    assert result["processed"] is True


def test_clear_events():
    bus = build()

    result = bus.clear_events()

    assert result["cleared"] is True


def test_history():
    bus = build()

    bus.publish_event({})

    assert len(bus.history()) == 1
