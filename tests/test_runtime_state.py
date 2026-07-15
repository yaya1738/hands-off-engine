from ai.factory.runtime_state import (
    FactoryRuntimeState,
)


def test_save_load(tmp_path):
    store = FactoryRuntimeState(
        tmp_path / "state.json"
    )

    store.save(
        {
            "cycle": 1,
        }
    )

    result = store.load()

    assert result["cycle"] == 1


def test_checkpoint(tmp_path):
    store = FactoryRuntimeState(
        tmp_path / "state.json"
    )

    result = store.checkpoint(
        {
            "cycle": 2,
        }
    )

    assert result["checkpoint"] is True


def test_restore_empty(tmp_path):
    store = FactoryRuntimeState(
        tmp_path / "state.json"
    )

    assert store.restore() == {}
