from ai.factory.state_store import FactoryStateStore


def test_state_save_and_load(tmp_path):
    path = tmp_path / "state.json"

    store = FactoryStateStore(
        str(path)
    )

    store.save(
        {
            "factory": "active",
            "builds": 1,
        }
    )

    result = store.load()

    assert result["factory"] == "active"
    assert result["builds"] == 1


def test_missing_state_returns_empty():
    store = FactoryStateStore(
        "does_not_exist.json"
    )

    assert store.load() == {}
