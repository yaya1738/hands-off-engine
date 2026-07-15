from ai.factory.autonomous_event_bus import (
    FactoryAutonomousEventBus,
)


def build():
    return FactoryAutonomousEventBus()


def test_publish():
    bus = build()

    result = bus.publish(
        {
            "type": "UPDATE",
        }
    )

    assert result["published"] is True


def test_subscribe():
    bus = build()

    result = bus.subscribe(
        "UPDATE",
        lambda event: None,
    )

    assert result["subscribed"] is True


def test_dispatch():
    bus = build()

    called = []

    bus.subscribe(
        "UPDATE",
        lambda event: called.append(event),
    )

    result = bus.dispatch(
        {
            "type": "UPDATE",
        }
    )

    assert result["handlers"] == 1
    assert len(called) == 1


def test_history():
    bus = build()

    bus.publish({})

    assert len(bus.history()) == 1
