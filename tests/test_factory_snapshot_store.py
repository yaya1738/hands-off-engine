from ai.factory.snapshot_store import (
    FactorySnapshotStore,
)


def test_save_snapshot():
    store = FactorySnapshotStore()

    store.save_snapshot(
        {
            "version": 1,
        }
    )

    result = store.get_latest()

    assert result["version"] == 1


def test_latest_snapshot():
    store = FactorySnapshotStore()

    store.save_snapshot(
        {
            "version": 1,
        }
    )

    store.save_snapshot(
        {
            "version": 2,
        }
    )

    result = store.get_latest()

    assert result["version"] == 2


def test_empty_store():
    store = FactorySnapshotStore()

    assert store.get_latest() is None
