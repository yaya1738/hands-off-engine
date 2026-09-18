from ai.factory.runtime_state import FactoryRuntimeState


def build():
    return FactoryRuntimeState()


def test_save_state():
    engine = build()

    result = engine.save_state(
        {"status": "running"}
    )

    assert result["saved"] is True


def test_load_state():
    engine = build()

    engine.save_state(
        {"status": "running"}
    )

    result = engine.load_state()

    assert result["loaded"] is True


def test_snapshot():
    engine = build()

    engine.save_state(
        {"status": "running"}
    )

    result = engine.snapshot()

    assert result["snapshotted"] is True


def test_restore():
    engine = build()

    result = engine.restore(
        {"status": "restored"}
    )

    assert result["restored"] is True


def test_history():
    engine = build()

    engine.save_state({})

    assert len(engine.history()) == 1


def test_load_state_does_not_grow_history():
    engine = build()
    engine.save_state({"status": "running"})
    before = len(engine.history())

    result = engine.load_state()

    assert result["loaded"] is True
    assert len(engine.history()) == before
