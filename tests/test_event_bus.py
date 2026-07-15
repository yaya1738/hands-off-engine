from ai.factory.event_bus import FactoryEventBus


def build():
    return FactoryEventBus()


def test_subscribe():
    engine = build()

    result = engine.subscribe(
        "test",
        lambda x: x,
    )

    assert result["subscribed"] is True


def test_publish_event():
    engine = build()

    result = engine.publish_event(
        "test",
        {},
    )

    assert result["published"] is True


def test_emit_runtime_event():
    engine = build()

    result = engine.emit_runtime_event(
        "runtime",
        {},
    )

    assert result["published"] is True


def test_process_events():
    engine = build()

    engine.publish_event(
        "test",
        {},
    )

    result = engine.process_events()

    assert result["processed"] is True


def test_history():
    engine = build()

    engine.publish_event(
        "test",
        {},
    )

    assert len(engine.history()) == 1
