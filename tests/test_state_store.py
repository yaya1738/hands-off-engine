from ai.factory.state_store import (
    FactoryStateStore,
)


def test_save_and_load(tmp_path):
    store = FactoryStateStore(
        tmp_path / "state.json"
    )

    store.save(
        {
            "mode": "AUTONOMOUS",
        }
    )

    result = store.load()

    assert result["mode"] == "AUTONOMOUS"


def test_snapshot(tmp_path):
    store = FactoryStateStore(
        tmp_path / "state.json"
    )

    store.save(
        {
            "health": "HEALTHY",
        }
    )

    assert store.snapshot()["health"] == "HEALTHY"


def test_clear(tmp_path):
    store = FactoryStateStore(
        tmp_path / "state.json"
    )

    store.save(
        {
            "test": True,
        }
    )

    store.clear()

    assert store.load() == {}
