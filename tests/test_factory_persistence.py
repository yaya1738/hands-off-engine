from ai.factory.persistence import (
    FactoryPersistence,
)


def test_save_and_load(tmp_path):
    store = FactoryPersistence(
        str(tmp_path / "state.json")
    )

    store.save(
        {
            "status": "HEALTHY",
        }
    )

    result = store.load()

    assert result["status"] == "HEALTHY"


def test_missing_state(tmp_path):
    store = FactoryPersistence(
        str(tmp_path / "missing.json")
    )

    assert store.load() is None


def test_clear(tmp_path):
    store = FactoryPersistence(
        str(tmp_path / "state.json")
    )

    store.save(
        {
            "version": 1,
        }
    )

    store.clear()

    assert store.exists() is False
