from ai.factory.event_intelligence import (
    FactoryEventIntelligence,
)


def build():
    return FactoryEventIntelligence()


def test_publish_event():
    engine = build()

    result = engine.publish_event(
        {}
    )

    assert result["published"] is True


def test_subscribe():
    engine = build()

    result = engine.subscribe(
        "update",
        "agent",
    )

    assert result["subscribed"] is True


def test_process_events():
    engine = build()

    result = engine.process_events()

    assert result["processed"] is True


def test_route_event():
    engine = build()

    result = engine.route_event(
        "update"
    )

    assert result["routed"] is True


def test_history():
    engine = build()

    engine.publish_event(
        {}
    )

    assert len(engine.history()) == 1
