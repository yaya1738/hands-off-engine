from ai.factory.event_replay import FactoryEventReplay


def build():
    return FactoryEventReplay()


def test_store_event():
    engine = build()

    result = engine.store_event(
        {"type": "runtime.started"}
    )

    assert result["stored"] is True


def test_query_events():
    engine = build()

    engine.store_event(
        {"type": "runtime.started"}
    )

    result = engine.query_events()

    assert result["queried"] is True


def test_replay_execution():
    engine = build()

    result = engine.replay_execution(
        []
    )

    assert result["replayed"] is True


def test_diagnose_run():
    engine = build()

    result = engine.diagnose_run(
        []
    )

    assert result["diagnosed"] is True


def test_history():
    engine = build()

    engine.store_event({})

    assert len(engine.history()) == 1
